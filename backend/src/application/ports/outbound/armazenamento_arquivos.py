"""Porta de saída para armazenamento durável de arquivos de evidência."""
from abc import ABC, abstractmethod


class ArmazenamentoArquivos(ABC):
    @abstractmethod
    async def salvar(self, conteudo: bytes, nome_original: str) -> str:
        """Persiste o conteúdo e devolve uma chave interna opaca."""
        ...
