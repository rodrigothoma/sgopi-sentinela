"""Armazenamento local de evidências atrás da porta hexagonal do RF22."""
from __future__ import annotations

import asyncio
from pathlib import Path
from uuid import uuid4

from application.ports.outbound.armazenamento_arquivos import ArmazenamentoArquivos


class ArmazenamentoDisco(ArmazenamentoArquivos):
    def __init__(self, diretorio: str | Path) -> None:
        self._diretorio = Path(diretorio)

    async def salvar(self, conteudo: bytes, nome_original: str) -> str:
        extensao = Path(nome_original).suffix.lower()
        chave = f"{uuid4().hex}{extensao}"

        def _gravar() -> None:
            self._diretorio.mkdir(parents=True, exist_ok=True)
            temporario = self._diretorio / f".{chave}.tmp"
            temporario.write_bytes(conteudo)
            temporario.replace(self._diretorio / chave)

        await asyncio.to_thread(_gravar)
        return chave
