"""Porta de saída: HasherSenha (RF11) — senha nunca em texto puro no banco."""
from abc import ABC, abstractmethod


class HasherSenha(ABC):
    @abstractmethod
    def gerar_hash(self, senha: str) -> str: ...

    @abstractmethod
    def verificar(self, senha: str, senha_hash: str) -> bool: ...
