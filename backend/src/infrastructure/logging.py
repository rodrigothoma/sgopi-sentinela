"""
Observabilidade (RNF09): logs JSON com request_id, usuario_id, operacao e duracao_ms.
Os valores de contexto são preenchidos pelo middleware HTTP e pela dependência de autenticação.
"""
from __future__ import annotations

import json
import logging
import re
import sys
from contextvars import ContextVar
from datetime import UTC, datetime

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
usuario_id_var: ContextVar[str | None] = ContextVar("usuario_id", default=None)

_CAMPOS_PADRAO = set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__) | {"message", "asctime"}

# RNF10: CPF nunca aparece em claro nos logs (formatado ou só dígitos)
_CPF_FORMATADO = re.compile(r"\b(\d{3})\.(\d{3})\.(\d{3})-(\d{2})\b")
_CPF_DIGITOS = re.compile(r"(?<!\d)(\d{3})(\d{3})(\d{3})(\d{2})(?!\d)")


def mascarar_cpfs(texto: str) -> str:
    texto = _CPF_FORMATADO.sub(r"***.***.\3-**", texto)
    return _CPF_DIGITOS.sub(r"*********\3**", texto)


class FormatadorJSON(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        corpo: dict[str, object] = {
            "ts": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": mascarar_cpfs(record.getMessage()),
            "request_id": request_id_var.get(),
            "usuario_id": usuario_id_var.get(),
        }
        for chave, valor in record.__dict__.items():
            if chave not in _CAMPOS_PADRAO and not chave.startswith("_"):
                corpo[chave] = mascarar_cpfs(valor) if isinstance(valor, str) else valor
        if record.exc_info:
            corpo["exc"] = mascarar_cpfs(self.formatException(record.exc_info))
        return json.dumps(corpo, default=str, ensure_ascii=False)


class FormatadorTexto(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        rid = request_id_var.get() or "-"
        base = f"{datetime.now(UTC).strftime('%H:%M:%S')} {record.levelname:<7} [{rid[:8]}] {record.name}: {mascarar_cpfs(record.getMessage())}"
        if record.exc_info:
            base += "\n" + mascarar_cpfs(self.formatException(record.exc_info))
        return base


def configurar_logging(json_logs: bool = True, level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(FormatadorJSON() if json_logs else FormatadorTexto())
    raiz = logging.getLogger()
    raiz.handlers = [handler]
    raiz.setLevel(level.upper())
    for ruidoso in ("uvicorn.access",):
        logging.getLogger(ruidoso).handlers = []
        logging.getLogger(ruidoso).propagate = False
