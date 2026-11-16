"""Adapter de entrada: /v1/auditoria (RNF03) — leitura e exportação CSV, somente Delegado/Supervisor."""
from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from adapters.inbound.http.deps import exigir_permissao
from adapters.inbound.http.exportacao_csv import FormatoExportacao, resposta_csv
from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_catalogo_auditoria import InterfaceListarCatalogoAuditoria
from application.ports.inbound.interface_consultar_auditoria import (
    LIMITE_MAXIMO_CONSULTA,
    LIMITE_PADRAO_CONSULTA,
    ConsultarAuditoriaInput,
    InterfaceConsultarAuditoria,
    RegistroAuditoriaOutput,
)
from application.ports.inbound.interface_registrar_exportacao import (
    InterfaceRegistrarExportacao,
    RecursoExportavel,
    RegistrarExportacaoInput,
)
from domain.usuario.permissoes import Permissao
from infrastructure.di import get_consultar_auditoria, get_listar_catalogo_auditoria, get_registrar_exportacao

router = APIRouter(prefix="/v1/auditoria", tags=["auditoria"])


class RegistroAuditoriaSchema(BaseModel):
    id: UUID
    quem: UUID | None
    quando: str
    operacao: str
    entidade: str
    entidade_id: str | None
    dados_antes: dict[str, Any] | None
    dados_depois: dict[str, Any] | None
    ip: str | None
    autor_nome: str | None = None
    autor_papel: str | None = None
    identificador_amigavel: str | None = None


class PaginaAuditoriaSchema(BaseModel):
    itens: list[RegistroAuditoriaSchema]
    total: int
    limit: int
    offset: int


class AcaoAuditadaSchema(BaseModel):
    operacao: str
    entidade: str


CABECALHO_CSV = (
    "quando", "operacao", "entidade", "identificador", "entidade_id",
    "autor_nome", "autor_papel", "autor_id", "ip", "dados_antes", "dados_depois",
)


def _linha_csv(r: RegistroAuditoriaOutput) -> tuple[Any, ...]:
    return (
        r.quando, r.operacao, r.entidade, r.identificador_amigavel, r.entidade_id,
        r.autor_nome, r.autor_papel, r.quem, r.ip, r.dados_antes, r.dados_depois,
    )


@router.get("/catalogo", response_model=list[AcaoAuditadaSchema])
async def listar_catalogo_auditoria(
    ator: Ator = Depends(exigir_permissao(Permissao.CONSULTAR_AUDITORIA)),
    use_case: InterfaceListarCatalogoAuditoria = Depends(get_listar_catalogo_auditoria),
) -> list[AcaoAuditadaSchema]:
    """Ações que podem aparecer na trilha (operação e entidade), geradas das classes de evento."""
    return [AcaoAuditadaSchema(operacao=a.operacao, entidade=a.entidade) for a in await use_case.executar(ator)]


@router.get("/exportar", response_class=StreamingResponse)
async def exportar_auditoria(
    formato: FormatoExportacao = Query(default=FormatoExportacao.CSV),
    entidade: str | None = Query(default=None),
    entidade_id: str | None = Query(default=None),
    operacao: str | None = Query(default=None),
    quem: UUID | None = Query(default=None),
    de: date | None = Query(default=None, description="Data inicial (inclusa), no fuso da operação"),
    ate: date | None = Query(default=None, description="Data final (inclusa), no fuso da operação"),
    limit: int = Query(default=LIMITE_MAXIMO_CONSULTA, ge=1, le=LIMITE_MAXIMO_CONSULTA),
    ator: Ator = Depends(exigir_permissao(Permissao.EXPORTAR_REGISTROS)),
    use_case: InterfaceConsultarAuditoria = Depends(get_consultar_auditoria),
    registrar_exportacao: InterfaceRegistrarExportacao = Depends(get_registrar_exportacao),
) -> StreamingResponse:
    """Exporta a trilha filtrada em CSV (Excel pt-BR). A própria exportação é auditada (RNF03)."""
    input_dto = ConsultarAuditoriaInput(
        entidade=entidade, entidade_id=entidade_id, operacao=operacao, quem=quem, limit=limit, de=de, ate=ate
    )
    registros = (await use_case.executar(ator, input_dto)).itens
    await registrar_exportacao.executar(
        ator,
        RegistrarExportacaoInput(
            recurso=RecursoExportavel.AUDITORIA,
            formato=formato.value,
            total_linhas=len(registros),
            filtros={
                "entidade": entidade, "entidade_id": entidade_id, "operacao": operacao, "quem": quem,
                "de": de, "ate": ate, "limit": limit,
            },
        ),
    )
    nome = f"auditoria_{datetime.now(UTC):%Y%m%d_%H%M%S}.csv"
    return resposta_csv(nome, CABECALHO_CSV, (_linha_csv(r) for r in registros))


@router.get("", response_model=PaginaAuditoriaSchema)
async def listar_auditoria(
    entidade: str | None = Query(default=None),
    entidade_id: str | None = Query(default=None),
    operacao: str | None = Query(default=None),
    quem: UUID | None = Query(default=None),
    de: date | None = Query(default=None, description="Data inicial (inclusa), no fuso da operação"),
    ate: date | None = Query(default=None, description="Data final (inclusa), no fuso da operação"),
    limit: int = Query(default=LIMITE_PADRAO_CONSULTA, ge=1, le=LIMITE_MAXIMO_CONSULTA),
    offset: int = Query(default=0, ge=0),
    ator: Ator = Depends(exigir_permissao(Permissao.CONSULTAR_AUDITORIA)),
    use_case: InterfaceConsultarAuditoria = Depends(get_consultar_auditoria),
) -> PaginaAuditoriaSchema:
    """Página da trilha de auditoria append-only (mais recente primeiro), com o total para a paginação."""
    pagina = await use_case.executar(
        ator,
        ConsultarAuditoriaInput(
            entidade=entidade, entidade_id=entidade_id, operacao=operacao, quem=quem,
            limit=limit, offset=offset, de=de, ate=ate,
        ),
    )
    return PaginaAuditoriaSchema(
        itens=[RegistroAuditoriaSchema(**r.__dict__) for r in pagina.itens],
        total=pagina.total,
        limit=pagina.limit,
        offset=pagina.offset,
    )
