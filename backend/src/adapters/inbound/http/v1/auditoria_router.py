"""Adapter de entrada: /v1/auditoria (RNF03) — leitura e exportação CSV, somente Delegado/Supervisor."""
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from adapters.inbound.http.deps import exigir_papel
from adapters.inbound.http.exportacao_csv import FormatoExportacao, resposta_csv
from application.ports.inbound.ator import Ator
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
from domain.usuario.entity import Papel
from infrastructure.di import get_consultar_auditoria, get_registrar_exportacao

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


CABECALHO_CSV = (
    "quando", "operacao", "entidade", "identificador", "entidade_id",
    "autor_nome", "autor_papel", "autor_id", "ip", "dados_antes", "dados_depois",
)


def _linha_csv(r: RegistroAuditoriaOutput) -> tuple[Any, ...]:
    return (
        r.quando, r.operacao, r.entidade, r.identificador_amigavel, r.entidade_id,
        r.autor_nome, r.autor_papel, r.quem, r.ip, r.dados_antes, r.dados_depois,
    )


@router.get("/exportar", response_class=StreamingResponse)
async def exportar_auditoria(
    formato: FormatoExportacao = Query(default=FormatoExportacao.CSV),
    entidade: str | None = Query(default=None),
    entidade_id: str | None = Query(default=None),
    operacao: str | None = Query(default=None),
    quem: UUID | None = Query(default=None),
    limit: int = Query(default=LIMITE_MAXIMO_CONSULTA, ge=1, le=LIMITE_MAXIMO_CONSULTA),
    ator: Ator = Depends(exigir_papel(Papel.DELEGADO, Papel.SUPERVISOR)),
    use_case: InterfaceConsultarAuditoria = Depends(get_consultar_auditoria),
    registrar_exportacao: InterfaceRegistrarExportacao = Depends(get_registrar_exportacao),
) -> StreamingResponse:
    """Exporta a trilha filtrada em CSV (Excel pt-BR). A própria exportação é auditada (RNF03)."""
    input_dto = ConsultarAuditoriaInput(entidade=entidade, entidade_id=entidade_id, operacao=operacao, quem=quem, limit=limit)
    registros = await use_case.executar(ator, input_dto)
    await registrar_exportacao.executar(
        ator,
        RegistrarExportacaoInput(
            recurso=RecursoExportavel.AUDITORIA,
            formato=formato.value,
            total_linhas=len(registros),
            filtros={"entidade": entidade, "entidade_id": entidade_id, "operacao": operacao, "quem": quem, "limit": limit},
        ),
    )
    nome = f"auditoria_{datetime.now(UTC):%Y%m%d_%H%M%S}.csv"
    return resposta_csv(nome, CABECALHO_CSV, (_linha_csv(r) for r in registros))


@router.get("", response_model=list[RegistroAuditoriaSchema])
async def listar_auditoria(
    entidade: str | None = Query(default=None),
    entidade_id: str | None = Query(default=None),
    operacao: str | None = Query(default=None),
    quem: UUID | None = Query(default=None),
    limit: int = Query(default=LIMITE_PADRAO_CONSULTA, ge=1, le=LIMITE_MAXIMO_CONSULTA),
    ator: Ator = Depends(exigir_papel(Papel.DELEGADO, Papel.SUPERVISOR)),
    use_case: InterfaceConsultarAuditoria = Depends(get_consultar_auditoria),
) -> list[RegistroAuditoriaSchema]:
    """Trilha de auditoria append-only (mais recente primeiro)."""
    registros = await use_case.executar(
        ator,
        ConsultarAuditoriaInput(
            entidade=entidade,
            entidade_id=entidade_id,
            operacao=operacao,
            quem=quem,
            limit=limit,
        ),
    )
    return [RegistroAuditoriaSchema(**r.__dict__) for r in registros]
