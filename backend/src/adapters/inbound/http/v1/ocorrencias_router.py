"""
Adapter de entrada: router HTTP /v1/ocorrencias (RF01*, RF13, RF04*, RF14, RF19).

Só este arquivo (e os demais routers) importa FastAPI — domain e application não sabem
da sua existência. Toda rota exige token; o ator vem do JWT, nunca do body.
"""
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from adapters.inbound.http.deps import exigir_papel
from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_registrar_ocorrencia_policial import (
    EnvolvidoInputDTO,
    InterfaceRegistrarOcorrenciaPolicial,
    RegistrarOcorrenciaInput,
    TipificacaoInputDTO,
)
from domain.usuario.entity import Papel
from infrastructure.di import get_registrar_ocorrencia

router = APIRouter(prefix="/v1/ocorrencias", tags=["ocorrencias"])


# ------------------------------------------------------------------ schemas
class TipificacaoSchema(BaseModel):
    artigo: str = Field(max_length=100)
    descricao: str = Field(max_length=500)


class EnvolvidoSchema(BaseModel):
    nome: str = Field(max_length=255)
    tipo: str  # VITIMA | TESTEMUNHA | SUSPEITO
    documento: str | None = Field(default=None, max_length=50)


class RegistrarOcorrenciaRequest(BaseModel):
    natureza: str = Field(max_length=255)
    descricao: str
    localizacao: str = Field(max_length=500)
    latitude: float
    longitude: float
    data_hora_fato: datetime
    tipificacoes: list[TipificacaoSchema] = []
    envolvidos: list[EnvolvidoSchema] = []


class OcorrenciaResponse(BaseModel):
    ocorrencia_id: str
    numero_protocolo: str
    status: str
    criada_em: str


# -------------------------------------------------------------------- rotas
@router.post("", response_model=OcorrenciaResponse, status_code=201)
@router.post("/", response_model=OcorrenciaResponse, status_code=201, include_in_schema=False)
async def registrar_ocorrencia(
    body: RegistrarOcorrenciaRequest,
    ator: Ator = Depends(exigir_papel(Papel.AGENTE)),
    use_case: InterfaceRegistrarOcorrenciaPolicial = Depends(get_registrar_ocorrencia),
) -> OcorrenciaResponse:
    """Registra uma nova ocorrência policial (RF01*). Somente AGENTE."""
    input_dto = RegistrarOcorrenciaInput(
        natureza=body.natureza,
        descricao=body.descricao,
        localizacao=body.localizacao,
        latitude=body.latitude,
        longitude=body.longitude,
        data_hora_fato=body.data_hora_fato,
        tipificacoes=tuple(TipificacaoInputDTO(artigo=t.artigo, descricao=t.descricao) for t in body.tipificacoes),
        envolvidos=tuple(EnvolvidoInputDTO(nome=e.nome, tipo=e.tipo, documento=e.documento) for e in body.envolvidos),
    )
    out = await use_case.executar(ator, input_dto)
    return OcorrenciaResponse(
        ocorrencia_id=str(out.ocorrencia_id), numero_protocolo=out.numero_protocolo, status=out.status, criada_em=out.criada_em
    )


# ------------------------------------------------ consulta (RF13) e revisão (RF04*, RF14)
from uuid import UUID  # noqa: E402

from fastapi import Query  # noqa: E402

from application.ports.inbound.interface_consultar_ocorrencias import (  # noqa: E402
    InterfaceListarOcorrencias,
    InterfaceObterDetalheOcorrencia,
    ListarOcorrenciasInput,
    OcorrenciaDetalheOutput,
    OcorrenciaResumoOutput,
)
from application.ports.inbound.interface_revisar_ocorrencia import (  # noqa: E402
    CorrigirOcorrenciaInput,
    DecisaoRevisaoInput,
    InterfaceCorrigirOcorrencia,
    InterfaceDevolverParaCorrecao,
    InterfaceReenviarOcorrencia,
    InterfaceRejeitarOcorrencia,
    InterfaceValidarOcorrencia,
)
from infrastructure.di import (  # noqa: E402
    get_corrigir_ocorrencia,
    get_devolver_para_correcao,
    get_listar_ocorrencias,
    get_obter_detalhe_ocorrencia,
    get_reenviar_ocorrencia,
    get_rejeitar_ocorrencia,
    get_validar_ocorrencia,
)

PAPEIS_CONSULTA = (Papel.AGENTE, Papel.DELEGADO, Papel.OPERADOR_CENTRAL, Papel.SUPERVISOR)


class OcorrenciaResumoSchema(BaseModel):
    ocorrencia_id: UUID
    numero_protocolo: str
    natureza: str
    localizacao: str
    latitude: float
    longitude: float
    status: str
    data_hora_fato: str
    criada_em: str
    atualizada_em: str
    agente_policial_id: UUID
    versao: int


class EnvolvidoDetalheSchema(BaseModel):
    id: UUID
    nome: str
    tipo: str
    documento: str | None


class HistoricoStatusSchema(BaseModel):
    de: str | None
    para: str
    em: str
    por_id: UUID
    justificativa: str | None


class OcorrenciaDetalheSchema(OcorrenciaResumoSchema):
    descricao: str
    validada_por_id: UUID | None
    justificativa_revisao: str | None
    desfecho: str | None
    hash_narrativa: str | None
    narrativa_integra: bool | None
    envolvidos: list[EnvolvidoDetalheSchema]
    tipificacoes: list[TipificacaoSchema]
    historico_status: list[HistoricoStatusSchema]


class PaginaOcorrenciasSchema(BaseModel):
    itens: list[OcorrenciaResumoSchema]
    total: int
    limit: int
    offset: int


class JustificativaRequest(BaseModel):
    justificativa: str = Field(min_length=1, max_length=2000)


class CorrigirOcorrenciaRequest(BaseModel):
    natureza: str | None = Field(default=None, max_length=255)
    descricao: str | None = None
    localizacao: str | None = Field(default=None, max_length=500)
    latitude: float | None = None
    longitude: float | None = None
    data_hora_fato: datetime | None = None
    envolvidos: list[EnvolvidoSchema] | None = None
    tipificacoes: list[TipificacaoSchema] | None = None


def _resumo(o: OcorrenciaResumoOutput) -> OcorrenciaResumoSchema:
    return OcorrenciaResumoSchema(**{k: getattr(o, k) for k in OcorrenciaResumoSchema.model_fields})


def _detalhe(o: OcorrenciaDetalheOutput) -> OcorrenciaDetalheSchema:
    base = {k: getattr(o, k) for k in OcorrenciaResumoSchema.model_fields}
    return OcorrenciaDetalheSchema(
        **base,
        descricao=o.descricao,
        validada_por_id=o.validada_por_id,
        justificativa_revisao=o.justificativa_revisao,
        desfecho=o.desfecho,
        hash_narrativa=o.hash_narrativa,
        narrativa_integra=o.narrativa_integra,
        envolvidos=[EnvolvidoDetalheSchema(id=e.id, nome=e.nome, tipo=e.tipo, documento=e.documento) for e in o.envolvidos],
        tipificacoes=[TipificacaoSchema(artigo=t.artigo, descricao=t.descricao) for t in o.tipificacoes],
        historico_status=[HistoricoStatusSchema(**h.__dict__) for h in o.historico_status],
    )


@router.get("", response_model=PaginaOcorrenciasSchema)
@router.get("/", response_model=PaginaOcorrenciasSchema, include_in_schema=False)
async def listar_ocorrencias(
    status: list[str] = Query(default=[]),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    somente_minhas: bool = Query(default=False),
    ator: Ator = Depends(exigir_papel(*PAPEIS_CONSULTA)),
    use_case: InterfaceListarOcorrencias = Depends(get_listar_ocorrencias),
) -> PaginaOcorrenciasSchema:
    """Lista ocorrências por status, da mais antiga para a mais nova (RF13). Agente só vê as próprias."""
    pagina = await use_case.executar(ator, ListarOcorrenciasInput(status=tuple(status), limit=limit, offset=offset, somente_minhas=somente_minhas))
    return PaginaOcorrenciasSchema(itens=[_resumo(i) for i in pagina.itens], total=pagina.total, limit=pagina.limit, offset=pagina.offset)


@router.get("/{ocorrencia_id}", response_model=OcorrenciaDetalheSchema)
async def obter_ocorrencia(
    ocorrencia_id: UUID,
    ator: Ator = Depends(exigir_papel(*PAPEIS_CONSULTA)),
    use_case: InterfaceObterDetalheOcorrencia = Depends(get_obter_detalhe_ocorrencia),
) -> OcorrenciaDetalheSchema:
    """Detalhe completo com envolvidos, tipificações e histórico de status (RF13)."""
    return _detalhe(await use_case.executar(ator, ocorrencia_id))


@router.post("/{ocorrencia_id}/validar", response_model=OcorrenciaDetalheSchema)
async def validar(
    ocorrencia_id: UUID,
    ator: Ator = Depends(exigir_papel(Papel.DELEGADO)),
    use_case: InterfaceValidarOcorrencia = Depends(get_validar_ocorrencia),
) -> OcorrenciaDetalheSchema:
    """AGUARDANDO_REVISAO → VALIDADA (RF04*). Somente DELEGADO."""
    return _detalhe(await use_case.executar(ator, DecisaoRevisaoInput(ocorrencia_id=ocorrencia_id)))


@router.post("/{ocorrencia_id}/devolver", response_model=OcorrenciaDetalheSchema)
async def devolver_para_correcao(
    ocorrencia_id: UUID,
    body: JustificativaRequest,
    ator: Ator = Depends(exigir_papel(Papel.DELEGADO)),
    use_case: InterfaceDevolverParaCorrecao = Depends(get_devolver_para_correcao),
) -> OcorrenciaDetalheSchema:
    """AGUARDANDO_REVISAO → EM_CORRECAO com justificativa (RF04*)."""
    return _detalhe(await use_case.executar(ator, DecisaoRevisaoInput(ocorrencia_id=ocorrencia_id, justificativa=body.justificativa)))


@router.post("/{ocorrencia_id}/rejeitar", response_model=OcorrenciaDetalheSchema)
async def rejeitar(
    ocorrencia_id: UUID,
    body: JustificativaRequest,
    ator: Ator = Depends(exigir_papel(Papel.DELEGADO)),
    use_case: InterfaceRejeitarOcorrencia = Depends(get_rejeitar_ocorrencia),
) -> OcorrenciaDetalheSchema:
    """AGUARDANDO_REVISAO → REJEITADA (terminal) com justificativa (RF04*)."""
    return _detalhe(await use_case.executar(ator, DecisaoRevisaoInput(ocorrencia_id=ocorrencia_id, justificativa=body.justificativa)))


@router.put("/{ocorrencia_id}", response_model=OcorrenciaDetalheSchema)
async def corrigir(
    ocorrencia_id: UUID,
    body: CorrigirOcorrenciaRequest,
    ator: Ator = Depends(exigir_papel(Papel.AGENTE)),
    use_case: InterfaceCorrigirOcorrencia = Depends(get_corrigir_ocorrencia),
) -> OcorrenciaDetalheSchema:
    """Edição pelo Agente autor, só em EM_CORRECAO (RF14)."""
    input_dto = CorrigirOcorrenciaInput(
        ocorrencia_id=ocorrencia_id,
        natureza=body.natureza,
        descricao=body.descricao,
        localizacao=body.localizacao,
        latitude=body.latitude,
        longitude=body.longitude,
        data_hora_fato=body.data_hora_fato,
        envolvidos=None if body.envolvidos is None else tuple(EnvolvidoInputDTO(nome=e.nome, tipo=e.tipo, documento=e.documento) for e in body.envolvidos),
        tipificacoes=None if body.tipificacoes is None else tuple(TipificacaoInputDTO(artigo=t.artigo, descricao=t.descricao) for t in body.tipificacoes),
    )
    return _detalhe(await use_case.executar(ator, input_dto))


@router.post("/{ocorrencia_id}/reenviar", response_model=OcorrenciaDetalheSchema)
async def reenviar(
    ocorrencia_id: UUID,
    ator: Ator = Depends(exigir_papel(Papel.AGENTE)),
    use_case: InterfaceReenviarOcorrencia = Depends(get_reenviar_ocorrencia),
) -> OcorrenciaDetalheSchema:
    """EM_CORRECAO → AGUARDANDO_REVISAO pelo Agente autor (RF14)."""
    return _detalhe(await use_case.executar(ator, ocorrencia_id))
