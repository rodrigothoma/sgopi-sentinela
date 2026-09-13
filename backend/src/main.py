"""
Ponto de entrada da aplicação FastAPI.

Aqui os adapters são instanciados e injetados nos use cases (Composition Root).
TODO: registrar routers e configurar injeção de dependência.
"""
from fastapi import FastAPI

app = FastAPI(
    title="SGOPI Sentinela",
    description="Sistema de Gestão de Ocorrências Policiais Integradas",
    version="0.1.0",
)


@app.get("/", tags=["health"])
async def health_check() -> dict:
    return {"status": "ok", "service": "SGOPI Sentinela API"}
