"""
Handlers globais de exceção (HEX-03, RNF08, RNF09).

Corpo padronizado: {"detail": <mensagem i18n>, "code": <chave>, "request_id": <id>, "extra": {...}}.
"""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from domain.shared.exceptions import (
    AcessoNegadoError,
    CampoObrigatorioError,
    ConflitoError,
    CredenciaisInvalidasError,
    DomainError,
    EntidadeNaoEncontradaError,
    TransicaoInvalidaError,
    ValorInvalidoError,
)
from infrastructure.i18n.translator import get_message
from infrastructure.logging import request_id_var

log = logging.getLogger("sgopi.http")

STATUS_POR_EXCECAO: tuple[tuple[type[DomainError], int], ...] = (
    (EntidadeNaoEncontradaError, 404),
    (CredenciaisInvalidasError, 401),
    (AcessoNegadoError, 403),
    (ConflitoError, 409),
    (TransicaoInvalidaError, 422),
    (CampoObrigatorioError, 422),
    (ValorInvalidoError, 422),
    (DomainError, 422),
)


def idioma(request: Request) -> str:
    return request.headers.get("Accept-Language", "pt")[:2].lower()


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None) or request_id_var.get()


def corpo_erro(request: Request, chave: str, status: int, extra: dict | None = None, mensagem: str | None = None) -> JSONResponse:
    rid = _request_id(request)
    conteudo: dict[str, object] = {
        "detail": mensagem or get_message(chave, idioma(request)),
        "code": chave,
        "request_id": rid,
    }
    if extra:
        conteudo["extra"] = extra
    headers: dict[str, str] = {}
    if status == 401:
        headers["WWW-Authenticate"] = "Bearer"
    if rid:
        headers["X-Request-ID"] = rid
    return JSONResponse(status_code=status, content=conteudo, headers=headers)


def _status_para(exc: DomainError) -> int:
    for tipo, status in STATUS_POR_EXCECAO:
        if isinstance(exc, tipo):
            return status
    return 422


def registrar_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def domain_handler(request: Request, exc: DomainError) -> JSONResponse:
        status = _status_para(exc)
        return corpo_erro(request, exc.chave, status, extra=exc.detalhes or None)

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        erros = [{"loc": list(e.get("loc", [])), "msg": e.get("msg"), "type": e.get("type")} for e in exc.errors()]
        return corpo_erro(request, "generic.validation_error", 422, extra={"errors": erros})

    @app.exception_handler(StarletteHTTPException)
    async def http_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        chave = {401: "auth.unauthorized", 403: "auth.forbidden", 404: "generic.not_found"}.get(exc.status_code, "generic.http_error")
        mensagem = exc.detail if isinstance(exc.detail, str) and exc.status_code not in (401, 403, 404) else None
        return corpo_erro(request, chave, exc.status_code, mensagem=mensagem)

    @app.exception_handler(Exception)
    async def generic_handler(request: Request, exc: Exception) -> JSONResponse:
        log.exception("erro não tratado", extra={"path": request.url.path, "request_id": _request_id(request)})
        return corpo_erro(request, "generic.internal_error", 500)
