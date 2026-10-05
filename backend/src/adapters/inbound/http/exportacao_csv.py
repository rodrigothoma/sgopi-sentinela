"""
Geração de CSV na borda HTTP (RNF03). O caso de uso devolve DTOs; aqui eles viram planilha.

- UTF-8 com BOM e separador ``;``: abre direto no Excel em pt-BR.
- CPF mascarado em toda célula (mesma regra dos logs — LGPD).
- Textos iniciados por ``= + - @`` recebem apóstrofo, neutralizando injeção de fórmula.
"""
import csv
import io
import json
from collections.abc import Iterable, Iterator, Sequence
from enum import Enum
from itertools import chain
from typing import Any

from fastapi.responses import StreamingResponse

from infrastructure.logging import mascarar_cpfs

BOM_UTF8 = "﻿"
SEPARADOR = ";"
MEDIA_TYPE_CSV = "text/csv; charset=utf-8"
_PREFIXOS_FORMULA = ("=", "+", "-", "@", "\t", "\r")


class FormatoExportacao(str, Enum):
    CSV = "csv"


def _celula(valor: Any) -> str:
    if valor is None:
        return ""
    if isinstance(valor, (int, float)):
        return str(valor)  # números (ex.: latitude negativa) não são fórmula
    texto = json.dumps(valor, ensure_ascii=False, default=str) if isinstance(valor, (dict, list)) else str(valor)
    texto = mascarar_cpfs(texto)
    return f"'{texto}" if texto.startswith(_PREFIXOS_FORMULA) else texto


def _linhas_csv(cabecalho: Sequence[str], linhas: Iterable[Sequence[Any]]) -> Iterator[str]:
    buffer = io.StringIO()
    escritor = csv.writer(buffer, delimiter=SEPARADOR, lineterminator="\r\n")
    yield BOM_UTF8
    for linha in chain([cabecalho], ([_celula(v) for v in linha] for linha in linhas)):
        escritor.writerow(linha)
        yield buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)


def resposta_csv(nome_arquivo: str, cabecalho: Sequence[str], linhas: Iterable[Sequence[Any]]) -> StreamingResponse:
    """``StreamingResponse`` pronta para download (``Content-Disposition: attachment``)."""
    return StreamingResponse(
        _linhas_csv(cabecalho, linhas),
        media_type=MEDIA_TYPE_CSV,
        headers={"Content-Disposition": f'attachment; filename="{nome_arquivo}"'},
    )
