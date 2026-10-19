"""
Adapter de entrada: /v1/laudos — Gestão de Laudos Periciais (RF07 / UC07 / sq07).
"""
from __future__ import annotations

from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, Response, UploadFile, status
from pydantic import BaseModel, Field

from adapters.inbound.http.deps import exigir_papel
from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_gerir_laudos import (
    AnexarLaudoInput,
    InterfaceAnexarLaudo,
    InterfaceBaixarArquivoLaudo,
    InterfaceListarLaudos,
    InterfaceObterLaudo,
    InterfaceSolicitarLaudo,
    LaudoOutput,
    SolicitarLaudoInput,
)
from domain.shared.exceptions import ValorInvalidoError
from domain.usuario.entity import Papel
from infrastructure.config.settings import settings
from infrastructure.di import (
    get_anexar_laudo,
    get_baixar_arquivo_laudo,
    get_listar_laudos,
    get_obter_laudo,
    get_solicitar_laudo,
)

router = APIRouter(prefix="/v1/laudos", tags=["laudos"])

PAPEIS_CONSULTA = (Papel.DELEGADO, Papel.PERITO, Papel.SUPERVISOR, Papel.OPERADOR_CENTRAL, Papel.AGENTE, Papel.ESCRIVAO)
PAPEIS_SOLICITACAO = (Papel.DELEGADO, Papel.PERITO)
PAPEIS_ANEXACAO = (Papel.PERITO, Papel.DELEGADO)


# ------------------------------------------------------------------ schemas
class SolicitarLaudoRequest(BaseModel):
    tipo_pericia: str = Field(description="Ex: BALISTICA, TOXICOLOGICA, LOCAL_CRIME, VEICULAR, NECROPSIA, etc.")
    descricao_solicitacao: str = Field(min_length=10, max_length=5000)
    ocorrencia_id: UUID | None = None
    inquerito_id: UUID | None = None
    item_apreendido_id: UUID | None = None


class LaudoSchema(BaseModel):
    id: UUID
    numero_referencia: str
    tipo_pericia: str
    descricao_solicitacao: str
    solicitante_id: UUID
    status: str
    solicitado_em: str
    atualizado_em: str
    perito_id: UUID | None = None
    ocorrencia_id: UUID | None = None
    inquerito_id: UUID | None = None
    item_apreendido_id: UUID | None = None
    conclusoes_tecnicas: str | None = None
    arquivo_nome: str | None = None
    hash_sha256: str | None = None
    concluido_em: str | None = None


class PaginaLaudosSchema(BaseModel):
    itens: list[LaudoSchema]
    total: int
    offset: int
    limit: int


def _laudo_schema(out: LaudoOutput) -> LaudoSchema:
    return LaudoSchema(
        id=out.id,
        numero_referencia=out.numero_referencia,
        tipo_pericia=out.tipo_pericia,
        descricao_solicitacao=out.descricao_solicitacao,
        solicitante_id=out.solicitante_id,
        status=out.status,
        solicitado_em=out.solicitado_em,
        atualizado_em=out.atualizado_em,
        perito_id=out.perito_id,
        ocorrencia_id=out.ocorrencia_id,
        inquerito_id=out.inquerito_id,
        item_apreendido_id=out.item_apreendido_id,
        conclusoes_tecnicas=out.conclusoes_tecnicas,
        arquivo_nome=out.arquivo_nome,
        hash_sha256=out.hash_sha256,
        concluido_em=out.concluido_em,
    )


# ------------------------------------------------------------------ endpoints
@router.post("", response_model=LaudoSchema, status_code=status.HTTP_201_CREATED)
async def solicitar_laudo(
    req: SolicitarLaudoRequest,
    ator: Ator = Depends(exigir_papel(*PAPEIS_SOLICITACAO)),
    uc: InterfaceSolicitarLaudo = Depends(get_solicitar_laudo),
) -> LaudoSchema:
    """Solicita a realização de perícia técnica à Polícia Científica."""
    resultado = await uc.executar(
        ator,
        SolicitarLaudoInput(
            tipo_pericia=req.tipo_pericia,
            descricao_solicitacao=req.descricao_solicitacao,
            ocorrencia_id=req.ocorrencia_id,
            inquerito_id=req.inquerito_id,
            item_apreendido_id=req.item_apreendido_id,
        ),
    )
    return _laudo_schema(resultado)


@router.get("", response_model=PaginaLaudosSchema)
async def listar_laudos(
    status_filtro: list[str] | None = Query(None, alias="status"),
    ocorrencia_id: UUID | None = Query(None),
    inquerito_id: UUID | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    ator: Ator = Depends(exigir_papel(*PAPEIS_CONSULTA)),
    uc: InterfaceListarLaudos = Depends(get_listar_laudos),
) -> PaginaLaudosSchema:
    """Lista laudos periciais com filtros e paginação."""
    itens, total = await uc.executar(
        ator,
        status=status_filtro,
        ocorrencia_id=ocorrencia_id,
        inquerito_id=inquerito_id,
        limit=limit,
        offset=offset,
    )
    return PaginaLaudosSchema(
        itens=[_laudo_schema(i) for i in itens],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/{laudo_id}", response_model=LaudoSchema)
async def obter_laudo(
    laudo_id: UUID,
    ator: Ator = Depends(exigir_papel(*PAPEIS_CONSULTA)),
    uc: InterfaceObterLaudo = Depends(get_obter_laudo),
) -> LaudoSchema:
    """Obtém detalhes do laudo pericial."""
    resultado = await uc.executar(ator, laudo_id)
    return _laudo_schema(resultado)


@router.post("/{laudo_id}/anexar", response_model=LaudoSchema)
async def anexar_laudo_concluido(
    laudo_id: UUID,
    conclusoes_tecnicas: str = Form(..., min_length=10),
    arquivo: UploadFile = File(...),
    ator: Ator = Depends(exigir_papel(*PAPEIS_ANEXACAO)),
    uc: InterfaceAnexarLaudo = Depends(get_anexar_laudo),
) -> LaudoSchema:
    """Homologa e anexa o arquivo PDF do laudo pericial com cálculo de hash SHA-256."""
    limite = settings.evidencias_tamanho_maximo_bytes
    conteudo = await arquivo.read(limite + 1)
    if not conteudo:
        raise ValorInvalidoError("O arquivo do laudo não pode ser vazio.", chave="laudo.arquivo_vazio")
    if len(conteudo) > limite:
        raise ValorInvalidoError(
            "O arquivo do laudo excede o tamanho máximo permitido.", chave="laudo.arquivo_grande", limite_bytes=limite
        )

    resultado = await uc.executar(
        ator,
        AnexarLaudoInput(
            laudo_id=laudo_id,
            conclusoes_tecnicas=conclusoes_tecnicas,
            conteudo_arquivo=conteudo,
            nome_arquivo=arquivo.filename or "laudo.pdf",
        ),
    )
    return _laudo_schema(resultado)


@router.get("/{laudo_id}/download")
async def download_arquivo_laudo(
    laudo_id: UUID,
    ator: Ator = Depends(exigir_papel(*PAPEIS_CONSULTA)),
    uc: InterfaceBaixarArquivoLaudo = Depends(get_baixar_arquivo_laudo),
) -> Response:
    """Download do PDF homologado do laudo; o conteúdo é conferido contra o SHA-256 antes da entrega."""
    arquivo = await uc.executar(ator, laudo_id)
    nome_codificado = quote(arquivo.nome_arquivo, safe="")
    return Response(
        content=arquivo.conteudo,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename*=UTF-8''{nome_codificado}",
            "X-Sha256": arquivo.hash_sha256,
            "X-Content-Type-Options": "nosniff",
        },
    )
