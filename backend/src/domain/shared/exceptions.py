"""
Exceções base do domínio.

Todas as exceções de regra de negócio herdam daqui. Nenhuma lib externa.
"""


class DomainError(Exception):
    """Erro base para violações de regra de negócio."""


class TransicaoInvalidaError(DomainError):
    """Levantada quando uma transição de estado não é permitida."""


class EntidadeNaoEncontradaError(DomainError):
    """Levantada quando uma entidade buscada não existe."""
