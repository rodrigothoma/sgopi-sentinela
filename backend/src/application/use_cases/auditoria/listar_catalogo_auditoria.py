"""Caso de uso: ListarCatalogoAuditoria (RNF03) — o filtro da trilha nunca fica desatualizado."""
from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_catalogo_auditoria import AcaoAuditadaOutput, InterfaceListarCatalogoAuditoria
from domain.auditoria import catalogo_eventos
from domain.usuario.permissoes import Permissao


class ListarCatalogoAuditoria(InterfaceListarCatalogoAuditoria):
    async def executar(self, ator: Ator) -> tuple[AcaoAuditadaOutput, ...]:
        ator.exigir(Permissao.CONSULTAR_AUDITORIA)
        return tuple(AcaoAuditadaOutput(operacao=op, entidade=entidade) for op, entidade in catalogo_eventos.catalogo())
