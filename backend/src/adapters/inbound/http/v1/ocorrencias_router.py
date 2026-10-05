"""
Adapter de entrada: router HTTP /v1/ocorrencias — registro policial e consulta (RF01*).

Só os routers importam FastAPI — domain e application não sabem da sua existência. Toda rota
exige token; o ator vem do JWT, nunca do body. O canal público, as evidências e a revisão do
Delegado ficam em ``ocorrencias_publico_router``, ``evidencias_router`` e ``revisao_router``;
os schemas compartilhados por eles moram aqui.
"""
from dataclasses import asdict, replace
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from adapters.inbound.http.deps import exigir_papel
from adapters.inbound.http.exportacao_csv import FormatoExportacao, resposta_csv
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
from application.ports.inbound.interface_linha_do_tempo import EventoLinhaDoTempoOutput, InterfaceLinhaDoTempo
from application.ports.inbound.interface_registrar_exportacao import (
    InterfaceRegistrarExportacao,
    RecursoExportavel,
    RegistrarExportacaoInput,
)
from application.ports.inbound.interface_registrar_ocorrencia_policial import (
    EnvolvidoInputDTO,
    InterfaceRegistrarOcorrenciaPolicial,
    ItemApreendidoInputDTO,
    RegistrarOcorrenciaInput,
    TipificacaoInputDTO,
)
from domain.usuario.entity import Papel
from infrastructure.di import (
    get_linha_do_tempo,
    get_listar_ocorrencias,
    get_obter_detalhe_ocorrencia,
    get_registrar_exportacao,
    get_registrar_ocorrencia,
)

router = APIRouter(prefix="/v1/ocorrencias", tags=["ocorrencias"])

PAPEIS_CONSULTA = (Papel.AGENTE, Papel.DELEGADO, Papel.OPERADOR_CENTRAL, Papel.SUPERVISOR)
PAPEIS_EXPORTACAO = (Papel.DELEGADO, Papel.SUPERVISOR)
TAMANHO_MAXIMO_BUSCA = 200
TAMANHO_PAGINA_EXPORTACAO = 200
LIMITE_EXPORTACAO = 5000


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
    # Sugestão #7 — opcional: ausente, o sistema sugere pela natureza/tipificações
    prioridade: str | None = Field(default=None, max_length=10)


class OcorrenciaResponse(BaseModel):
    ocorrencia_id: str
    numero_protocolo: str
    status: str
    criada_em: str
    prioridade: str | None = None  # só no registro policial; o canal público não expõe a triagem


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
    prioridade: str = "MEDIA"


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


class EventoLinhaDoTempoSchema(BaseModel):
    em: str
    tipo: str
    por_id: UUID | None = None
    por_nome: str | None = None
    detalhes: dict[str, Any]


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
        prioridade=body.prioridade,
    )
    out = await use_case.executar(ator, input_dto)
    return OcorrenciaResponse(
        ocorrencia_id=str(out.ocorrencia_id),
        numero_protocolo=out.numero_protocolo,
        status=out.status,
        criada_em=out.criada_em,
        prioridade=out.prioridade,
    )



def filtros_listagem(
    status: list[str] = Query(default=[]),
    somente_minhas: bool = Query(default=False),
    mais_recentes_primeiro: bool = Query(default=False),
    ordenar_por_prioridade: bool = Query(default=False),
    natureza: str | None = Query(default=None, max_length=TAMANHO_MAXIMO_BUSCA),
    protocolo: str | None = Query(default=None, max_length=TAMANHO_MAXIMO_BUSCA),
    texto: str | None = Query(default=None, max_length=TAMANHO_MAXIMO_BUSCA),
    origem: str | None = Query(default=None, max_length=20),
    data_fato_de: datetime | None = Query(default=None),
    data_fato_ate: datetime | None = Query(default=None),
) -> ListarOcorrenciasInput:
    """Filtros comuns à listagem e à exportação; a paginação é aplicada por cada rota."""
    return ListarOcorrenciasInput(
        status=tuple(status),
        somente_minhas=somente_minhas,
        mais_recentes_primeiro=mais_recentes_primeiro,
        ordenar_por_prioridade=ordenar_por_prioridade,
        natureza=natureza,
        protocolo=protocolo,
        texto=texto,
        origem=origem,
        data_fato_de=data_fato_de,
        data_fato_ate=data_fato_ate,
    )


@router.get("", response_model=PaginaOcorrenciasSchema)
@router.get("/", response_model=PaginaOcorrenciasSchema, include_in_schema=False)
async def listar_ocorrencias(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    filtros: ListarOcorrenciasInput = Depends(filtros_listagem),
    ator: Ator = Depends(exigir_papel(*PAPEIS_CONSULTA)),
    use_case: InterfaceListarOcorrencias = Depends(get_listar_ocorrencias),
) -> PaginaOcorrenciasSchema:
    """Lista ocorrências por status, da mais antiga para a mais nova (RF01), ou o inverso com
    ``mais_recentes_primeiro``; ``ordenar_por_prioridade`` põe as mais graves antes. Aceita busca por natureza, protocolo, texto (descrição/localização),
    origem e período do fato. Agente só vê as próprias."""
    pagina = await use_case.executar(ator, replace(filtros, limit=limit, offset=offset))
    return PaginaOcorrenciasSchema(itens=[_resumo(i) for i in pagina.itens], total=pagina.total, limit=pagina.limit, offset=pagina.offset)


CABECALHO_CSV = (
    "numero_protocolo", "natureza", "status", "prioridade", "origem", "data_hora_fato", "localizacao",
    "latitude", "longitude", "criada_em", "atualizada_em", "agente_policial_id", "inquerito_id",
)


def _linha_csv(o: OcorrenciaResumoOutput) -> tuple[object, ...]:
    return tuple(getattr(o, coluna) for coluna in CABECALHO_CSV)


async def _todas_as_paginas(
    use_case: InterfaceListarOcorrencias, ator: Ator, filtros: ListarOcorrenciasInput
) -> list[OcorrenciaResumoOutput]:
    """Percorre a listagem paginada até esgotá-la ou atingir o teto de exportação."""
    itens: list[OcorrenciaResumoOutput] = []
    while len(itens) < LIMITE_EXPORTACAO:
        pagina = await use_case.executar(ator, replace(filtros, limit=TAMANHO_PAGINA_EXPORTACAO, offset=len(itens)))
        itens.extend(pagina.itens)
        if not pagina.itens or len(itens) >= pagina.total:
            break
    return itens[:LIMITE_EXPORTACAO]


@router.get("/exportar", response_class=StreamingResponse)
async def exportar_ocorrencias(
    formato: FormatoExportacao = Query(default=FormatoExportacao.CSV),
    filtros: ListarOcorrenciasInput = Depends(filtros_listagem),
    ator: Ator = Depends(exigir_papel(*PAPEIS_EXPORTACAO)),
    use_case: InterfaceListarOcorrencias = Depends(get_listar_ocorrencias),
    registrar_exportacao: InterfaceRegistrarExportacao = Depends(get_registrar_exportacao),
) -> StreamingResponse:
    """Exporta a listagem filtrada em CSV (até ``LIMITE_EXPORTACAO`` linhas). Somente Delegado/Supervisor;
    a exportação é auditada (RNF03)."""
    itens = await _todas_as_paginas(use_case, ator, filtros)
    await registrar_exportacao.executar(
        ator,
        RegistrarExportacaoInput(
            recurso=RecursoExportavel.OCORRENCIAS,
            formato=formato.value,
            total_linhas=len(itens),
            filtros={k: v for k, v in asdict(filtros).items() if k not in ("limit", "offset")},
        ),
    )
    nome = f"ocorrencias_{datetime.now(UTC):%Y%m%d_%H%M%S}.csv"
    return resposta_csv(nome, CABECALHO_CSV, (_linha_csv(o) for o in itens))


@router.get("/{ocorrencia_id}", response_model=OcorrenciaDetalheSchema)
async def obter_ocorrencia(
    ocorrencia_id: UUID,
    ator: Ator = Depends(exigir_papel(*PAPEIS_CONSULTA)),
    use_case: InterfaceObterDetalheOcorrencia = Depends(get_obter_detalhe_ocorrencia),
) -> OcorrenciaDetalheSchema:
    """Detalhe completo com envolvidos, tipificações e histórico de status (RF01)."""
    return _detalhe(await use_case.executar(ator, ocorrencia_id))


def _evento_schema(e: EventoLinhaDoTempoOutput) -> EventoLinhaDoTempoSchema:
    return EventoLinhaDoTempoSchema(em=e.em, tipo=e.tipo.value, por_id=e.por_id, por_nome=e.por_nome, detalhes=e.detalhes)


@router.get("/{ocorrencia_id}/linha-do-tempo", response_model=list[EventoLinhaDoTempoSchema])
async def linha_do_tempo(
    ocorrencia_id: UUID,
    ator: Ator = Depends(exigir_papel(*PAPEIS_CONSULTA)),
    use_case: InterfaceLinhaDoTempo = Depends(get_linha_do_tempo),
) -> list[EventoLinhaDoTempoSchema]:
    """Status, despachos, evidências, apreensões, inquérito e laudos em ordem cronológica (sugestão #12)."""
    return [_evento_schema(e) for e in await use_case.executar(ator, ocorrencia_id)]
