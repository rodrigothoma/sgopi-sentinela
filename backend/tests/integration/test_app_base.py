"""Integração: /health, handlers de erro padronizados, request_id e CORS (RNF02*, RNF08, RNF09)."""
from fastapi import APIRouter

from domain.shared.exceptions import (
    AcessoNegadoError,
    ConflitoError,
    CredenciaisInvalidasError,
    EntidadeNaoEncontradaError,
    ValorInvalidoError,
)


async def test_health_reporta_db_up(client):
    r = await client.get("/health")
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["status"] == "ok" and corpo["db"] == "up"
    assert corpo["request_id"] == r.headers["X-Request-ID"]


async def test_health_degradado_quando_banco_cai(app, client):
    from infrastructure.database.connection import get_session

    class SessaoQuebrada:
        async def execute(self, *_):
            raise RuntimeError("connection refused")

    async def _quebrada():
        yield SessaoQuebrada()

    app.dependency_overrides[get_session] = _quebrada
    r = await client.get("/health")
    assert r.status_code == 503
    assert r.json()["db"] == "down"


async def test_request_id_do_cliente_e_propagado(client):
    r = await client.get("/health", headers={"X-Request-ID": "abc-123"})
    assert r.headers["X-Request-ID"] == "abc-123"
    assert r.json()["request_id"] == "abc-123"


async def test_handlers_de_dominio_mapeiam_status_e_i18n(app, client):
    router = APIRouter()

    @router.get("/_teste/{tipo}")
    async def _levanta(tipo: str):
        raise {
            "nf": EntidadeNaoEncontradaError("x", chave="ocorrencia.not_found"),
            "403": AcessoNegadoError("x"),
            "401": CredenciaisInvalidasError("x", chave="auth.credenciais_invalidas"),
            "409": ConflitoError("x"),
            "422": ValorInvalidoError("x", chave="ocorrencia.descricao_curta", minimo=20),
        }[tipo]

    app.include_router(router)

    r = await client.get("/_teste/nf")
    assert r.status_code == 404 and r.json() == {"detail": "Ocorrência não encontrada", "code": "ocorrencia.not_found", "request_id": r.headers["X-Request-ID"]}

    r = await client.get("/_teste/nf", headers={"Accept-Language": "en-US"})
    assert r.json()["detail"] == "Occurrence not found"

    assert (await client.get("/_teste/403")).status_code == 403
    r = await client.get("/_teste/401")
    assert r.status_code == 401 and r.headers["WWW-Authenticate"] == "Bearer"
    assert (await client.get("/_teste/409")).status_code == 409
    r = await client.get("/_teste/422")
    assert r.status_code == 422
    assert r.json()["code"] == "ocorrencia.descricao_curta" and r.json()["extra"] == {"minimo": 20}


async def test_validation_error_tem_corpo_padronizado(app, client):
    router = APIRouter()

    @router.get("/_teste_param/{n}")
    async def _p(n: int):
        return {"n": n}

    app.include_router(router)
    r = await client.get("/_teste_param/abc")
    assert r.status_code == 422
    corpo = r.json()
    assert corpo["code"] == "generic.validation_error" and corpo["extra"]["errors"][0]["loc"] == ["path", "n"]


async def test_rota_inexistente_404_padronizado(client):
    r = await client.get("/nao-existe")
    assert r.status_code == 404 and r.json()["code"] == "generic.not_found"


async def test_cors_por_lista_de_origens(client):
    ok = await client.options("/health", headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET"})
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:3000"
    negado = await client.options("/health", headers={"Origin": "http://malicioso.example", "Access-Control-Request-Method": "GET"})
    assert "access-control-allow-origin" not in negado.headers
