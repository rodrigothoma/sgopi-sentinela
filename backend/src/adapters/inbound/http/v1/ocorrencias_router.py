"""
Adapter de entrada: router HTTP /v1/ocorrencias — registro policial e consulta (RF01*).

Só os routers importam FastAPI — domain e application não sabem da sua existência. Toda rota
exige token; o ator vem do JWT, nunca do body. O canal público, as evidências e a revisão do
Delegado ficam em ``ocorrencias_publico_router``, ``evidencias_router`` e ``revisao_router``;
os schemas compartilhados por eles moram aqui.
"""
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from adapters.inbound.http.deps import exigir_papel
from adapters.inbound.http.v1.apreensoes_router import ItemApreendidoSchema, RegistrarItemApreendidoRequest, item_schema
from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_acessar_evidencia import EstadoIntegridadeEvidencia
from application.ports.inbound.interface_consultar_ocorrencias import (
    InterfaceListarOcorrencias,
    InterfaceObterDetalheOcorrencia,
    ListarOcorrenciasInput,
    OcorrenciaDetalheOutput,
    OcorrenciaResumoOutput,
)
from application.ports.inbound.interface_registrar_ocorrencia_policial import (
    EnvolvidoInputDTO,
    InterfaceRegistrarOcorrenciaPolicial,
    ItemApreendidoInputDTO,
    RegistrarOcorrenciaInput,
    TipificacaoInputDTO,
)
from domain.usuario.entity import Papel
from infrastructure.di import get_listar_ocorrencias, get_obter_detalhe_ocorrencia, get_registrar_ocorrencia

router = APIRouter(prefix="/v1/ocorrencias", tags=["ocorrencias"])

PAPEIS_CONSULTA = (Papel.AGENTE, Papel.DELEGADO, Papel.OPERADOR_CENTRAL, Papel.SUPERVISOR)


# ------------------------------------------------------------------ schemas
class TipificacaoSchema(BaseModel):
    artigo: str = Field(max_length=100)
    descricao: str = Field(max_length=500)


class EnvolvidoSchema(BaseModel):
    nome: str = Field(max_length=255)
    tipo: str  # VITIMA | TESTEMUNHA | SUSPEITO | COMUNICANTE
    documento: str | None = Field(default=None, max_length=50)
    email: str | None = Field(default=None, max_length=255)
    telefone: str | None = Field(default=None, max_length=30)


class RegistrarOcorrenciaRequest(BaseModel):
    natureza: str = Field(max_length=255)
    descricao: str
    localizacao: str = Field(max_length=500)
    latitude: float
    longitude: float
    data_hora_fato: datetime
    tipificacoes: list[TipificacaoSchema] = []
    envolvidos: list[EnvolvidoSchema] = []
    # RF03 — opcional: apreensão concomitante ao registro (mesma transação; lacre único na base)
    itens_apreendidos: list[RegistrarItemApreendidoRequest] = []


class OcorrenciaResponse(BaseModel):
    ocorrencia_id: str
    numero_protocolo: str
    status: str
    criada_em: str


class EvidenciaSchema(BaseModel):
    id: UUID
    nome_original: str
    formato: str
    tamanho: int
    hash_sha256: str
    enviada_em: str


class IntegridadeEvidenciaSchema(BaseModel):
    evidencia_id: UUID
    estado: EstadoIntegridadeEvidencia
    hash_armazenado: str
    hash_recalculado: str
    verificado_em: str




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
    inquerito_id: UUID | None = None
    origem: str = "POLICIAL"


class EnvolvidoDetalheSchema(BaseModel):
    id: UUID
    nome: str
    tipo: str
    documento: str | None = None
    email: str | None = None
    telefone: str | None = None


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
    chave_autenticidade: str | None
    arquivada_por_id: UUID | None
    motivo_arquivamento: str | None
    excluida_por_id: UUID | None
    motivo_exclusao: str | None
    envolvidos: list[EnvolvidoDetalheSchema]
    tipificacoes: list[TipificacaoSchema]
    evidencias: list[EvidenciaSchema]
    itens_apreendidos: list[ItemApreendidoSchema]
    historico_status: list[HistoricoStatusSchema]


class PaginaOcorrenciasSchema(BaseModel):
    itens: list[OcorrenciaResumoSchema]
    total: int
    limit: int
    offset: int


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
        chave_autenticidade=o.chave_autenticidade,
        arquivada_por_id=o.arquivada_por_id,
        motivo_arquivamento=o.motivo_arquivamento,
        excluida_por_id=o.excluida_por_id,
        motivo_exclusao=o.motivo_exclusao,
        envolvidos=[
            EnvolvidoDetalheSchema(
                id=e.id, nome=e.nome, tipo=e.tipo, documento=e.documento, email=e.email, telefone=e.telefone
            )
            for e in o.envolvidos
        ],
        tipificacoes=[TipificacaoSchema(artigo=t.artigo, descricao=t.descricao) for t in o.tipificacoes],
        evidencias=[EvidenciaSchema(**e.__dict__) for e in o.evidencias],
        itens_apreendidos=[item_schema(i) for i in o.itens_apreendidos],
        historico_status=[HistoricoStatusSchema(**h.__dict__) for h in o.historico_status],
    )


def _envolvido_dto(e: EnvolvidoSchema) -> EnvolvidoInputDTO:
    return EnvolvidoInputDTO(nome=e.nome, tipo=e.tipo, documento=e.documento, email=e.email, telefone=e.telefone)



# -------------------------------------------------------------------- rotas
@router.post("", response_model=OcorrenciaResponse, status_code=201)
@router.post("/", response_model=OcorrenciaResponse, status_code=201, include_in_schema=False)
async def registrar_ocorrencia(
    body: RegistrarOcorrenciaRequest,
    ator: Ator = Depends(exigir_papel(Papel.AGENTE)),
    use_case: InterfaceRegistrarOcorrenciaPolicial = Depends(get_registrar_ocorrencia),
) -> OcorrenciaResponse:
    """Registra uma nova ocorrência policial (RF01*), opcionalmente já com itens apreendidos (RF03). Somente AGENTE."""
    input_dto = RegistrarOcorrenciaInput(
        natureza=body.natureza,
        descricao=body.descricao,
        localizacao=body.localizacao,
        latitude=body.latitude,
        longitude=body.longitude,
        data_hora_fato=body.data_hora_fato,
        tipificacoes=tuple(TipificacaoInputDTO(artigo=t.artigo, descricao=t.descricao) for t in body.tipificacoes),
        envolvidos=tuple(_envolvido_dto(e) for e in body.envolvidos),
        itens_apreendidos=tuple(ItemApreendidoInputDTO(**i.model_dump()) for i in body.itens_apreendidos),
    )
    out = await use_case.executar(ator, input_dto)
    return OcorrenciaResponse(
        ocorrencia_id=str(out.ocorrencia_id), numero_protocolo=out.numero_protocolo, status=out.status, criada_em=out.criada_em
    )



@router.get("", response_model=PaginaOcorrenciasSchema)
@router.get("/", response_model=PaginaOcorrenciasSchema, include_in_schema=False)
async def listar_ocorrencias(
    status: list[str] = Query(default=[]),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    somente_minhas: bool = Query(default=False),
    mais_recentes_primeiro: bool = Query(default=False),
    ator: Ator = Depends(exigir_papel(*PAPEIS_CONSULTA)),
    use_case: InterfaceListarOcorrencias = Depends(get_listar_ocorrencias),
) -> PaginaOcorrenciasSchema:
    """Lista ocorrências por status, da mais antiga para a mais nova (RF01), ou o inverso com
    ``mais_recentes_primeiro``. Agente só vê as próprias."""
    pagina = await use_case.executar(
        ator,
        ListarOcorrenciasInput(
            status=tuple(status),
            limit=limit,
            offset=offset,
            somente_minhas=somente_minhas,
            mais_recentes_primeiro=mais_recentes_primeiro,
        ),
    )
    return PaginaOcorrenciasSchema(itens=[_resumo(i) for i in pagina.itens], total=pagina.total, limit=pagina.limit, offset=pagina.offset)


@router.get("/{ocorrencia_id}", response_model=OcorrenciaDetalheSchema)
async def obter_ocorrencia(
    ocorrencia_id: UUID,
    ator: Ator = Depends(exigir_papel(*PAPEIS_CONSULTA)),
    use_case: InterfaceObterDetalheOcorrencia = Depends(get_obter_detalhe_ocorrencia),
) -> OcorrenciaDetalheSchema:
    """Detalhe completo com envolvidos, tipificações e histórico de status (RF01)."""
    return _detalhe(await use_case.executar(ator, ocorrencia_id))
