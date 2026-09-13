"""
Composition Root — ponto de entrada da aplicação FastAPI.

Registra routers e configura exception handlers globais com mensagens i18n.
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from adapters.inbound.http.v1.ocorrencias_router import router as ocorrencias_router
from domain.shared.exceptions import EntidadeNaoEncontradaError, TransicaoInvalidaError
from infrastructure.i18n.translator import get_message

app = FastAPI(
    title="SGOPI Sentinela",
    description="Sistema de Gestão de Ocorrências Policiais Integradas",
    version="0.1.0",
)

app.include_router(ocorrencias_router)


def _lang(request: Request) -> str:
    return request.headers.get("Accept-Language", "pt")[:2]


@app.exception_handler(EntidadeNaoEncontradaError)
async def not_found_handler(request: Request, exc: EntidadeNaoEncontradaError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": get_message("ocorrencia.not_found", _lang(request))})


@app.exception_handler(TransicaoInvalidaError)
async def transition_handler(request: Request, exc: TransicaoInvalidaError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": get_message("ocorrencia.invalid_transition", _lang(request))})


@app.get("/health", tags=["health"])
async def health() -> dict:
    """Health check — verifica que o servidor está no ar."""
    return {"status": "ok", "service": "SGOPI Sentinela API"}
