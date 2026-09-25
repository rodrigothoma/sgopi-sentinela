"""
Ponto de entrada da aplicação FastAPI.

Cria o app, registra middleware, routers e handlers globais. O *wiring* de
portas/adapters fica em ``infrastructure/di.py``. O esquema do banco é gerido
por Alembic (``alembic upgrade head``) — não há ``create_all`` aqui (HEX-11).
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.inbound.http.erros import registrar_handlers
from adapters.inbound.http.middleware import RequestIdMiddleware
from infrastructure.config.settings import settings
from infrastructure.database.connection import get_session
from infrastructure.logging import configurar_logging, request_id_var

log = logging.getLogger("sgopi")


def criar_app() -> FastAPI:
    configurar_logging(json_logs=settings.log_json, level=settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        log.info("SGOPI Sentinela iniciando", extra={"app_env": settings.app_env})
        if settings.gerador_ocorrencias_ligado:
            from infrastructure.di import gerador_ocorrencias

            # Sem simulador-demo no banco: loga 'rode o seed', não inicia, servidor segue no ar.
            await gerador_ocorrencias.ligar()
        yield
        from infrastructure.di import gerador_ocorrencias, simulador

        # Ajuste 8: cancela e aguarda as tasks do gerador e do simulador.
        await gerador_ocorrencias.desligar()
        await simulador.desligar()
        log.info("SGOPI Sentinela encerrando")

    app = FastAPI(
        title="SGOPI Sentinela",
        description="Sistema de Gestão de Ocorrências Policiais Integradas",
        version="0.2.0",
        lifespan=lifespan,
    )

    # RNF02*: CORS por lista de origens (nunca "*" com credenciais — DIV-25)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )
    app.add_middleware(RequestIdMiddleware)
    registrar_handlers(app)
    _registrar_routers(app)

    @app.get("/health", tags=["health"])
    async def health(session: AsyncSession = Depends(get_session)) -> JSONResponse:
        """Health check (RNF09): verifica o servidor e a conexão com o banco."""
        try:
            await session.execute(text("SELECT 1"))
            db = "up"
        except Exception as exc:  # noqa: BLE001 — qualquer falha de banco degrada o serviço
            log.error("health: banco indisponível: %s", exc)
            db = "down"
        corpo = {
            "status": "ok" if db == "up" else "degraded",
            "service": "SGOPI Sentinela API",
            "db": db,
            "request_id": request_id_var.get(),
        }
        return JSONResponse(status_code=200 if db == "up" else 503, content=corpo)

    return app


def _registrar_routers(app: FastAPI) -> None:
    """Routers são registrados aqui; cada etapa do MVP adiciona os seus."""
    from adapters.inbound.http.v1.apreensoes_router import router as apreensoes_router
    from adapters.inbound.http.v1.auditoria_router import router as auditoria_router
    from adapters.inbound.http.v1.auth_router import router as auth_router
    from adapters.inbound.http.v1.ocorrencias_router import router as ocorrencias_router
    from adapters.inbound.http.v1.usuarios_router import router as usuarios_router
    from adapters.inbound.http.v1.despacho_router import router as despacho_router
    from adapters.inbound.http.v1.viaturas_router import router as viaturas_router
    from adapters.inbound.websocket.tempo_real_router import router as tempo_real_router

    app.include_router(auth_router)
    app.include_router(usuarios_router)
    app.include_router(ocorrencias_router)
    app.include_router(apreensoes_router)
    app.include_router(auditoria_router)
    app.include_router(viaturas_router)
    app.include_router(despacho_router)
    app.include_router(tempo_real_router)


app = criar_app()
