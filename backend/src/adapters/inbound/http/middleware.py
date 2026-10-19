"""Middleware de correlação e log de requisições."""
from __future__ import annotations

import logging
import re
import time
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from infrastructure.logging import request_id_var, usuario_id_var

log = logging.getLogger("sgopi.http")

# O id do cliente vai para os logs: só aceita um token curto e sem quebras/controles (log injection)
_REQUEST_ID_VALIDO = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


def request_id_de(valor: str | None) -> str:
    return valor if valor and _REQUEST_ID_VALIDO.fullmatch(valor) else uuid4().hex


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        rid = request_id_de(request.headers.get("X-Request-ID"))
        request.state.request_id = rid  # sobrevive ao reset do ContextVar (handler de 500 roda fora deste middleware)
        token_rid = request_id_var.set(rid)
        token_uid = usuario_id_var.set(None)
        inicio = time.perf_counter()
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
        finally:
            duracao_ms = round((time.perf_counter() - inicio) * 1000, 2)
            log.info(
                "%s %s -> %s (%.2f ms)",
                request.method,
                request.url.path,
                status,
                duracao_ms,
                extra={"operacao": f"{request.method} {request.url.path}", "status": status, "duracao_ms": duracao_ms},
            )
            request_id_var.reset(token_rid)
            usuario_id_var.reset(token_uid)
        response.headers["X-Request-ID"] = rid
        return response
