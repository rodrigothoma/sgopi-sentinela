"""Middleware de correlação e log de requisições."""
from __future__ import annotations

import logging
import time
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from infrastructure.logging import request_id_var, usuario_id_var

log = logging.getLogger("sgopi.http")


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get("X-Request-ID") or uuid4().hex
        request.state.request_id = rid  # sobrevive ao reset do ContextVar (handler de 500 roda fora deste middleware)
        token_rid = request_id_var.set(rid)
        token_uid = usuario_id_var.set(None)
        inicio = time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            duracao_ms = round((time.perf_counter() - inicio) * 1000, 2)
            status = locals().get("response").status_code if "response" in locals() else 500
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
