"""
Integração WebSocket (RF17): token inválido recusado; painel recebe OcorrenciaValidada e
PosicaoAtualizada sem refresh. Usa o TestClient síncrono do Starlette (httpx não fala WS);
o banco SQLite é criado dentro do loop do servidor de teste.
"""
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

from infrastructure.database.connection import Base, get_session
from infrastructure.database.models import UsuarioModel
from tests.integration.conftest import IDS, PAPEIS, SENHA_PADRAO


@pytest.fixture
def client_ws():
    from adapters.outbound.seguranca.hasher_argon2 import HasherArgon2
    from main import criar_app

    app = criar_app()
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    estado = {"pronto": False}

    async def _get_session():
        if not estado["pronto"]:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            hash_ = HasherArgon2().gerar_hash(SENHA_PADRAO)
            async with factory() as s:
                for login, uid in IDS.items():
                    s.add(UsuarioModel(id=uid, nome=login, login=login, senha_hash=hash_, papel=PAPEIS[login], ativo=True))
                await s.commit()
            estado["pronto"] = True
        async with factory() as s:
            yield s

    app.dependency_overrides[get_session] = _get_session
    with TestClient(app) as c:
        yield c


def _token(c: TestClient, login: str) -> str:
    return c.post("/v1/auth/login", json={"login": login, "senha": SENHA_PADRAO}).json()["access_token"]


def test_token_invalido_e_recusado(client_ws):
    from starlette.websockets import WebSocketDisconnect

    with pytest.raises(WebSocketDisconnect) as exc:
        with client_ws.websocket_connect("/v1/tempo-real?token=lixo"):
            pass
    assert exc.value.code == 1008
    with pytest.raises(WebSocketDisconnect):
        with client_ws.websocket_connect("/v1/tempo-real"):
            pass


def test_painel_recebe_eventos_de_validacao_e_posicao(client_ws):
    c = client_ws
    ta, td, to = _token(c, "agente"), _token(c, "delegado"), _token(c, "operador")
    ha, hd, ho = ({"Authorization": f"Bearer {t}"} for t in (ta, td, to))

    o = c.post(
        "/v1/ocorrencias",
        json={
            "natureza": "Roubo", "descricao": "Roubo a transeunte com uso de arma branca.", "localizacao": "Centro",
            "latitude": -29.78, "longitude": -55.79, "data_hora_fato": (datetime.now(UTC) - timedelta(hours=1)).isoformat(),
            "envolvidos": [{"nome": "V", "tipo": "VITIMA"}],
        },
        headers=ha,
    ).json()
    v = c.post("/v1/viaturas", json={"prefixo": "VTR-01", "placa": "IAB1A23"}, headers=ho).json()

    with c.websocket_connect(f"/v1/tempo-real?token={to}") as ws:
        r = c.post(f"/v1/ocorrencias/{o['ocorrencia_id']}/validar", headers=hd)
        assert r.status_code == 200
        msg = ws.receive_json()
        assert msg["tipo"] == "OcorrenciaValidada" and msg["dados"]["ocorrencia_id"] == o["ocorrencia_id"]
        assert msg["dados"]["latitude"] == -29.78

        r = c.post("/v1/telemetria/posicoes", json={"viatura_id": v["id"], "latitude": -29.70, "longitude": -55.70, "registrada_em": datetime.now(UTC).isoformat()}, headers=ho)
        assert r.status_code == 200
        msg = ws.receive_json()
        assert msg["tipo"] == "PosicaoAtualizada" and msg["dados"]["prefixo"] == "VTR-01" and msg["dados"]["longitude"] == -55.70
