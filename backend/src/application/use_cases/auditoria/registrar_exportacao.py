"""Caso de uso: RegistrarExportacao (RNF03) — a própria exportação entra na trilha de auditoria."""
from typing import Any

from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_registrar_exportacao import (
    InterfaceRegistrarExportacao,
    RegistrarExportacaoInput,
)
from application.ports.outbound.porta_auditoria import PortaAuditoria
from application.ports.outbound.relogio import Relogio
from application.ports.outbound.unidade_de_trabalho import UnidadeDeTrabalho
from domain.auditoria.entity import RegistroAuditoria
from domain.usuario.entity import Papel

PAPEIS_EXPORTACAO = (Papel.DELEGADO, Papel.SUPERVISOR)
ENTIDADE_EXPORTACAO = "Exportacao"


def _serializavel(valor: Any) -> Any:
    """O registro de auditoria é JSON: UUIDs, datas e enums viram texto; listas são preservadas."""
    if isinstance(valor, (list, tuple)):
        return [_serializavel(v) for v in valor]
    if valor is None or isinstance(valor, (str, int, float, bool)):
        return valor
    return str(valor)


def _filtros_aplicados(filtros: dict[str, Any]) -> dict[str, Any]:
    return {chave: _serializavel(valor) for chave, valor in filtros.items() if valor not in (None, "", [], ())}


class RegistrarExportacao(InterfaceRegistrarExportacao):
    def __init__(self, auditoria: PortaAuditoria, uow: UnidadeDeTrabalho, relogio: Relogio) -> None:
        self._auditoria = auditoria
        self._uow = uow
        self._relogio = relogio

    async def executar(self, ator: Ator, input_dto: RegistrarExportacaoInput) -> None:
        ator.exigir_papel(*PAPEIS_EXPORTACAO)
        filtros = _filtros_aplicados(input_dto.filtros)
        async with self._uow:
            await self._auditoria.registrar(
                RegistroAuditoria(
                    quem=ator.id,
                    quando=self._relogio.agora(),
                    operacao=f"{input_dto.recurso.value}.exportar",
                    entidade=ENTIDADE_EXPORTACAO,
                    entidade_id=input_dto.recurso.value,
                    dados_depois={
                        "formato": input_dto.formato,
                        "filtros": filtros,
                        "total_linhas": input_dto.total_linhas,
                    },
                    ip=ator.ip,
                )
            )
            await self._uow.commit()
