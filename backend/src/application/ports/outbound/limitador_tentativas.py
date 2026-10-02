"""
Porta de saída: LimitadorTentativas (RNF02 — proteção contra força bruta e abuso).

Conta tentativas por chave (p.ex. ``login|ip`` ou o IP de origem) numa janela deslizante;
ao atingir o máximo, a chave fica bloqueada por um período. A política (máximo, janela,
bloqueio) é da implementação concreta, configurada no Composition Root.
"""
from abc import ABC, abstractmethod
from datetime import datetime


class LimitadorTentativas(ABC):
    @abstractmethod
    def bloqueado_ate(self, chave: str, agora: datetime) -> datetime | None:
        """Instante em que o bloqueio da chave expira, ou None se ela pode tentar."""
        ...

    @abstractmethod
    def registrar(self, chave: str, agora: datetime) -> None:
        """Contabiliza uma tentativa; ao atingir o máximo na janela, bloqueia a chave."""
        ...

    @abstractmethod
    def limpar(self, chave: str) -> None:
        """Zera tentativas e bloqueio da chave (p.ex. após login bem-sucedido)."""
        ...
