"""
Adapter de entrada: router HTTP /v1/ocorrencias (RF01*, RF13, RF04*, RF14, RF19).

Só este arquivo (e os demais routers) importa FastAPI — domain e application não sabem
da sua existência. Toda rota exige token; o ator vem do JWT, nunca do body.
"""
from datetime import datetime
from uuid import UUID
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field

from adapters.inbound.http.deps import exigir_papel
from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_anexar_evidencia import (
    AnexarEvidenciaInput,
    EvidenciaOutput,
    InterfaceAnexarEvidencia,
)
from application.ports.inbound.interface_acessar_evidencia import (
    EstadoIntegridadeEvidencia,
    InterfaceObterEvidenciaParaDownload,
    InterfaceVerificarIntegridadeEvidencia,
)
from application.ports.inbound.interface_registrar_ocorrencia_policial import (
    EnvolvidoInputDTO,
    InterfaceRegistrarOcorrenciaPolicial,
    RegistrarOcorrenciaInput,
    TipificacaoInputDTO,
)
from application.ports.outbound.repositorio_usuario import RepositorioUsuario
from domain.usuario.entity import Papel
from infrastructure.config.settings import settings
from infrastructure.database.connection import get_session
from infrastructure.di import (
    get_anexar_evidencia,
    get_obter_evidencia_para_download,
    get_registrar_ocorrencia,
    get_repositorio_usuario,
    get_verificar_integridade_evidencia,
)
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/v1/ocorrencias", tags=["ocorrencias"])


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


class RegistrarOcorrenciaPublicaRequest(BaseModel):
    nome_solicitante: str = Field(min_length=3, max_length=255)
    natureza: str = Field(max_length=255)
    descricao: str = Field(min_length=20, max_length=500)
    localizacao: str = Field(max_length=500)
    latitude: float
    longitude: float
    data_hora_fato: datetime
    documento: str = Field(min_length=5, max_length=50)
    email: str = Field(min_length=5, max_length=255)
    telefone: str = Field(min_length=8, max_length=30)
    declaracao_maioridade: bool = True


class ConsultaPublicaResponse(BaseModel):
    numero_protocolo: str
    status: str
    natureza: str
    localizacao: str
    criada_em: str
    desfecho: str | None = None


# -------------------------------------------------------------------- rotas
@router.post("/publico", response_model=OcorrenciaResponse, status_code=201)
async def registrar_ocorrencia_publica(
    body: RegistrarOcorrenciaPublicaRequest,
    use_case: InterfaceRegistrarOcorrenciaPolicial = Depends(get_registrar_ocorrencia),
    usuario_repo: RepositorioUsuario = Depends(get_repositorio_usuario),
) -> OcorrenciaResponse:
    """Permite ao cidadão registrar uma ocorrência pública sem autenticação prévia."""
    from fastapi import HTTPException
    from domain.shared.documentos import cpf_valido, normalizar_cpf

    if not body.declaracao_maioridade:
        raise HTTPException(
            status_code=422,
            detail="É obrigatório confirmar a declaração de maioridade (+18 anos) e veracidade dos fatos.",
        )

    doc_limpo = normalizar_cpf(body.documento)
    if len(doc_limpo) == 11 and not cpf_valido(doc_limpo):
        raise HTTPException(
            status_code=422,
            detail="O CPF informado é inválido. Por favor, confira os números digitados.",
        )

    agente = await usuario_repo.buscar_por_login("agente")
    if not agente:
        from uuid import uuid4
        ator = Ator(id=uuid4(), login="cidadao_web", papel=Papel.AGENTE)
    else:
        ator = Ator(id=agente.id, login="cidadao_web", papel=Papel.AGENTE)

    input_dto = RegistrarOcorrenciaInput(
        natureza=body.natureza,
        descricao=body.descricao.strip(),
        localizacao=body.localizacao,
        latitude=body.latitude,
        longitude=body.longitude,
        data_hora_fato=body.data_hora_fato,
        tipificacoes=(),
        envolvidos=(
            EnvolvidoInputDTO(
                nome=body.nome_solicitante.strip(),
                tipo="COMUNICANTE",
                documento=body.documento.strip(),
                email=body.email.strip(),
                telefone=body.telefone.strip(),
            ),
        ),
    )
    out = await use_case.executar(ator, input_dto)
    return OcorrenciaResponse(
        ocorrencia_id=str(out.ocorrencia_id),
        numero_protocolo=out.numero_protocolo,
        status=out.status,
        criada_em=out.criada_em,
    )


@router.get("/publico/{protocolo}", response_model=ConsultaPublicaResponse)
async def consultar_ocorrencia_publica(
    protocolo: str,
    session: AsyncSession = Depends(get_session),
) -> ConsultaPublicaResponse:
    """Permite ao cidadão consultar o status simplificado de sua ocorrência por protocolo."""
    from fastapi import HTTPException
    from infrastructure.database.models import OcorrenciaModel
    from sqlalchemy import select

    stmt = select(OcorrenciaModel).where(OcorrenciaModel.numero_protocolo == protocolo.strip())
    model = (await session.execute(stmt)).scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Ocorrência não encontrada com o protocolo informado.")

    return ConsultaPublicaResponse(
        numero_protocolo=model.numero_protocolo,
        status=model.status,
        natureza=model.natureza,
        localizacao=model.localizacao,
        criada_em=model.criada_em.isoformat() if hasattr(model.criada_em, "isoformat") else str(model.criada_em),
        desfecho=model.desfecho,
    )


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


@router.post("/{ocorrencia_id}/evidencias", response_model=EvidenciaSchema, status_code=201)
async def anexar_evidencia(
    ocorrencia_id: UUID,
    arquivo: UploadFile = File(...),
    ator: Ator = Depends(exigir_papel(Papel.AGENTE)),
    use_case: InterfaceAnexarEvidencia = Depends(get_anexar_evidencia),
) -> EvidenciaSchema:
    """Anexa PDF/JPEG/PNG de até 10 MB à ocorrência do agente autor (RF22)."""
    try:
        conteudo = await arquivo.read(settings.evidencias_tamanho_maximo_bytes + 1)
    finally:
        await arquivo.close()
    out = await use_case.executar(
        ator,
        AnexarEvidenciaInput(
            ocorrencia_id=ocorrencia_id,
            nome_arquivo=arquivo.filename or "",
            tipo_mime=arquivo.content_type or "",
            conteudo=conteudo,
        ),
    )
    return EvidenciaSchema(**out.__dict__)


PAPEIS_CONSULTA = (Papel.AGENTE, Papel.DELEGADO, Papel.OPERADOR_CENTRAL, Papel.SUPERVISOR)
MIME_EVIDENCIA = {
    "pdf": "application/pdf",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
}


@router.get(
    "/{ocorrencia_id}/evidencias/{evidencia_id}/integridade",
    response_model=IntegridadeEvidenciaSchema,
)
async def verificar_integridade_evidencia(
    ocorrencia_id: UUID,
    evidencia_id: UUID,
    ator: Ator = Depends(exigir_papel(*PAPEIS_CONSULTA)),
    use_case: InterfaceVerificarIntegridadeEvidencia = Depends(get_verificar_integridade_evidencia),
) -> IntegridadeEvidenciaSchema:
    out = await use_case.executar(ator, ocorrencia_id, evidencia_id)
    return IntegridadeEvidenciaSchema(**out.__dict__)


@router.get("/{ocorrencia_id}/evidencias/{evidencia_id}/download")
async def download_evidencia(
    ocorrencia_id: UUID,
    evidencia_id: UUID,
    ator: Ator = Depends(exigir_papel(*PAPEIS_CONSULTA)),
    use_case: InterfaceObterEvidenciaParaDownload = Depends(get_obter_evidencia_para_download),
) -> Response:
    out = await use_case.executar(ator, ocorrencia_id, evidencia_id)
    nome_codificado = quote(out.nome_original, safe="")
    return Response(
        content=out.conteudo,
        media_type=MIME_EVIDENCIA[out.formato],
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{nome_codificado}",
            "Content-Length": str(len(out.conteudo)),
            "X-Content-Type-Options": "nosniff",
        },
    )


# ------------------------------------------------ consulta (RF13) e revisão (RF04*, RF14)
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
    envolvidos: list[EnvolvidoDetalheSchema]
    tipificacoes: list[TipificacaoSchema]
    evidencias: list[EvidenciaSchema]
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
        chave_autenticidade=o.chave_autenticidade,
        envolvidos=[
            EnvolvidoDetalheSchema(
                id=e.id,
                nome=e.nome,
                tipo=e.tipo,
                documento=e.documento,
                email=e.email,
                telefone=e.telefone,
            )
            for e in o.envolvidos
        ],
        tipificacoes=[TipificacaoSchema(artigo=t.artigo, descricao=t.descricao) for t in o.tipificacoes],
        evidencias=[EvidenciaSchema(**e.__dict__) for e in o.evidencias],
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
