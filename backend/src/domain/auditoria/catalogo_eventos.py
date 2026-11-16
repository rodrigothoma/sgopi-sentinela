"""
Catálogo das ações auditadas, gerado a partir das classes de evento (RNF03).

As classes se registram sozinhas ao serem declaradas (``EventoAuditoria.__init_subclass__``);
este módulo só garante que todos os módulos de eventos foram importados antes da leitura.
A lista abaixo é de **módulos**, não de operações: uma ação nova entra no catálogo apenas por
existir como subclasse num desses módulos.
"""
from __future__ import annotations

from domain.auditoria import exportacao as _exportacao  # noqa: F401
from domain.auditoria.evento import EventoAuditoria
from domain.despacho import auditoria as _despacho  # noqa: F401
from domain.inquerito import auditoria as _inquerito  # noqa: F401
from domain.interagencias import auditoria as _interagencias  # noqa: F401
from domain.laudo import auditoria as _laudo  # noqa: F401
from domain.medida_protetiva import auditoria as _medida  # noqa: F401
from domain.notificacao import auditoria as _notificacao  # noqa: F401
from domain.ocorrencia import auditoria as _ocorrencia  # noqa: F401
from domain.ocorrencia import auditoria_provas as _provas  # noqa: F401
from domain.usuario import auditoria as _usuario  # noqa: F401
from domain.viatura import auditoria as _viatura  # noqa: F401


def catalogo() -> tuple[tuple[str, str], ...]:
    """(operação, entidade) de todas as ações auditadas, em ordem alfabética."""
    return EventoAuditoria.catalogo()


def entidades() -> tuple[str, ...]:
    return tuple(sorted({entidade for _, entidade in catalogo()}))


def grafias(operacao: str) -> tuple[str, ...]:
    return EventoAuditoria.grafias(operacao)


def grafias_da_entidade(entidade: str) -> tuple[str, ...]:
    return EventoAuditoria.grafias_da_entidade(entidade)
