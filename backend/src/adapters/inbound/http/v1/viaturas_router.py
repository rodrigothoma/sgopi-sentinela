"""Adapter de entrada: /v1/viaturas, /v1/telemetria e /v1/simulador (RF02)."""
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, Field

from adapters.inbound.http.deps import ator_opcional, exigir_papel
from adapters.inbound.simulador.orquestrador_despacho import OrquestradorDespacho
from adapters.inbound.simulador.simulador_telemetria import SimuladorTelemetria
from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_gerir_viaturas import (
    AlterarSituacaoInput,
    CadastrarViaturaInput,
    InterfaceAlterarSituacaoViatura,
    InterfaceCadastrarViatura,
    InterfaceEmitirCredencialTelemetria,
    InterfaceListarViaturas,
    InterfaceRegistrarPosicaoViatura,
    RegistrarPosicaoInput,
    ViaturaOutput,
)
from application.ports.outbound.credencial_dispositivo import CredencialDispositivo
from domain.shared.exceptions import AcessoNegadoError, CredenciaisInvalidasError
from domain.usuario.entity import Papel
from infrastructure.config.settings import settings
from infrastructure.di import (
    get_alterar_situacao_viatura,
    get_cadastrar_viatura,
    get_credencial_dispositivo,
    get_emitir_credencial_telemetria,
    get_listar_viaturas,
    get_orquestrador_despacho,
    get_registrar_posicao_viatura,
    get_simulador,
)

router = APIRouter(tags=["viaturas"])
GESTAO = (Papel.OPERADOR_CENTRAL, Papel.SUPERVISOR)
CONSULTA = (Papel.OPERADOR_CENTRAL, Papel.SUPERVISOR, Papel.DELEGADO, Papel.AGENTE)


class ViaturaSchema(BaseModel):
    id: UUID
    prefixo: str
    placa: str
    situacao: str
    latitude: float | None
    longitude: float | None
    posicao_registrada_em: str | None
    sinal: str
    versao: int


class CadastrarViaturaRequest(BaseModel):
    prefixo: str = Field(min_length=1, max_length=20)
    placa: str = Field(min_length=1, max_length=10)


class AlterarSituacaoRequest(BaseModel):
    situacao: str  # DISPONIVEL | INDISPONIVEL


class PosicaoRequest(BaseModel):
    viatura_id: UUID
    latitude: float
    longitude: float
    registrada_em: datetime


def _schema(v: ViaturaOutput) -> ViaturaSchema:
    return ViaturaSchema(**v.__dict__)


@router.get("/v1/viaturas", response_model=list[ViaturaSchema])
async def listar_viaturas(ator: Ator = Depends(exigir_papel(*CONSULTA)), uc: InterfaceListarViaturas = Depends(get_listar_viaturas)):
    """Frota com última posição e indicador de sinal (RF02, RNF04*)."""
    return [_schema(v) for v in await uc.executar(ator)]


@router.post("/v1/viaturas", response_model=ViaturaSchema, status_code=201)
async def cadastrar_viatura(body: CadastrarViaturaRequest, ator: Ator = Depends(exigir_papel(*GESTAO)), uc: InterfaceCadastrarViatura = Depends(get_cadastrar_viatura)):
    """Cadastra viatura; prefixo/placa duplicados → 409 (RF02)."""
    return _schema(await uc.executar(ator, CadastrarViaturaInput(prefixo=body.prefixo, placa=body.placa)))


@router.patch("/v1/viaturas/{viatura_id}/situacao", response_model=ViaturaSchema)
async def alterar_situacao(viatura_id: UUID, body: AlterarSituacaoRequest, ator: Ator = Depends(exigir_papel(*GESTAO)), uc: InterfaceAlterarSituacaoViatura = Depends(get_alterar_situacao_viatura)):
    """DISPONIVEL ⇄ INDISPONIVEL manual (RF02)."""
    return _schema(await uc.executar(ator, AlterarSituacaoInput(viatura_id=viatura_id, situacao=body.situacao)))


CABECALHO_CREDENCIAL_DISPOSITIVO = "X-Credencial-Dispositivo"


class CredencialTelemetriaResponse(BaseModel):
    viatura_id: UUID
    credencial: str
    cabecalho: str = CABECALHO_CREDENCIAL_DISPOSITIVO


def _autoria_da_posicao(
    viatura_id: UUID, credencial: str | None, credenciais: CredencialDispositivo, ator: Ator | None
) -> tuple[str, UUID | None]:
    """(origem, por_id): o rastreador só envia a própria viatura; token humano só fora de produção (N12)."""
    if credencial is not None:
        if not credenciais.confere(viatura_id, credencial):
            raise CredenciaisInvalidasError("Credencial de dispositivo inválida para esta viatura.", chave="auth.unauthorized")
        return f"dispositivo:{viatura_id}", None
    if ator is None:
        raise CredenciaisInvalidasError("Credencial ausente.", chave="auth.unauthorized")
    if not settings.telemetria_humana_permitida:
        raise AcessoNegadoError(
            "Em produção a telemetria só é aceita do rastreador da viatura.", chave="telemetria.exige_dispositivo"
        )
    ator.exigir_papel(*GESTAO)
    return f"http:{ator.login}", ator.id


@router.post("/v1/telemetria/posicoes", response_model=ViaturaSchema, tags=["telemetria"])
async def registrar_posicao(
    body: PosicaoRequest,
    credencial: str | None = Header(default=None, alias=CABECALHO_CREDENCIAL_DISPOSITIVO),
    credenciais: CredencialDispositivo = Depends(get_credencial_dispositivo),
    ator: Ator | None = Depends(ator_opcional),
    uc: InterfaceRegistrarPosicaoViatura = Depends(get_registrar_posicao_viatura),
):
    """Ingestão de posição GPS (RF02). Timestamp fora de ±60 s → 422; posição anterior é mantida.

    Autenticação: ``X-Credencial-Dispositivo`` do rastreador (presa à viatura) ou, fora de produção,
    Bearer de OPERADOR_CENTRAL/SUPERVISOR. A origem e o autor vão para a auditoria da chegada ao local.
    """
    origem, por_id = _autoria_da_posicao(body.viatura_id, credencial, credenciais, ator)
    return _schema(
        await uc.executar(
            RegistrarPosicaoInput(
                viatura_id=body.viatura_id, latitude=body.latitude, longitude=body.longitude,
                registrada_em=body.registrada_em, origem=origem, por_id=por_id,
            )
        )
    )


@router.post("/v1/viaturas/{viatura_id}/credencial-telemetria", response_model=CredencialTelemetriaResponse, tags=["telemetria"])
async def emitir_credencial_telemetria(
    viatura_id: UUID,
    ator: Ator = Depends(exigir_papel(*GESTAO)),
    uc: InterfaceEmitirCredencialTelemetria = Depends(get_emitir_credencial_telemetria),
) -> CredencialTelemetriaResponse:
    """Credencial a gravar no rastreador GPS da viatura (emissão auditada)."""
    return CredencialTelemetriaResponse(viatura_id=viatura_id, credencial=await uc.executar(ator, viatura_id))


@router.get("/v1/simulador", tags=["telemetria"])
async def status_simulador(
    ator: Ator = Depends(exigir_papel(*CONSULTA)),
    sim: SimuladorTelemetria = Depends(get_simulador),
    orq: OrquestradorDespacho = Depends(get_orquestrador_despacho),
) -> dict:
    """Estado do simulador + orquestrador de despacho automático."""
    return {**sim.status(), "orquestrador": orq.status()}


@router.post("/v1/simulador/ligar", tags=["telemetria"])
async def ligar_simulador(
    ator: Ator = Depends(exigir_papel(*GESTAO)),
    sim: SimuladorTelemetria = Depends(get_simulador),
    orq: OrquestradorDespacho = Depends(get_orquestrador_despacho),
) -> dict:
    """Liga o simulador de telemetria a 1 Hz (RF02) e, se habilitado por flag, o despacho automático."""
    if not settings.simulador_habilitado:
        raise AcessoNegadoError(
            "O simulador de telemetria é recurso de demonstração e fica desabilitado em produção.",
            chave="simulador.desabilitado_em_producao",
        )
    sim.ligar()
    if settings.despacho_automatico_ligado:
        await orq.ligar()
    return {**sim.status(), "orquestrador": orq.status()}


@router.post("/v1/simulador/desligar", tags=["telemetria"])
async def desligar_simulador(
    ator: Ator = Depends(exigir_papel(*GESTAO)),
    sim: SimuladorTelemetria = Depends(get_simulador),
    orq: OrquestradorDespacho = Depends(get_orquestrador_despacho),
) -> dict:
    """Desliga o simulador e o orquestrador de despacho automático juntos."""
    await sim.desligar()
    await orq.desligar()
    return {**sim.status(), "orquestrador": orq.status()}
