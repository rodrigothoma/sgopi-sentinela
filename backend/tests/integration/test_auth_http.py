"""Integração HTTP: login, token, RBAC e auditoria de negação (RNF02*, RNF03)."""
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from infrastructure.database.models import RegistroAuditoriaModel
from tests.integration.conftest import IDS, SENHA_PADRAO
from tests.integration.helpers import auth, corpo_ocorrencia, token_de


async def test_login_ok_devolve_token_e_usuario(client):
    r = await client.post("/v1/auth/login", json={"login": "delegado", "senha": SENHA_PADRAO})
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["token_type"] == "bearer" and corpo["usuario"]["papel"] == "DELEGADO"
    assert corpo["usuario"]["id"] == str(IDS["delegado"])


async def test_login_invalido_401_i18n(client):
    r = await client.post("/v1/auth/login", json={"login": "agente", "senha": "errada"}, headers={"Accept-Language": "en"})
    assert r.status_code == 401
    assert r.json() == {"detail": "Invalid login or password", "code": "auth.credenciais_invalidas", "request_id": r.headers["X-Request-ID"]}


async def test_usuario_inativo_nao_autentica(client):
    r = await client.post("/v1/auth/login", json={"login": "inativo", "senha": SENHA_PADRAO})
    assert r.status_code == 401


async def test_rota_protegida_sem_token_401(client):
    r = await client.get("/v1/auth/me")
    assert r.status_code == 401 and r.headers["WWW-Authenticate"] == "Bearer"


async def test_me_devolve_ator_do_token(client):
    r = await client.get("/v1/auth/me", headers=await auth(client, "operador"))
    assert r.status_code == 200 and r.json()["papel"] == "OPERADOR_CENTRAL"


async def test_token_adulterado_401(client):
    token = await token_de(client, "agente")
    r = await client.get("/v1/auth/me", headers={"Authorization": f"Bearer {token[:-3]}xyz"})
    assert r.status_code == 401 and r.json()["code"] == "auth.token_invalido"


async def test_token_expirado_401(app, client):
    from infrastructure.config.settings import settings
    from infrastructure.di import get_relogio
    from tests.fakes.portas_fake import RelogioFake

    token = await token_de(client, "agente")
    horas = settings.jwt_expires_in_hours + 1
    app.dependency_overrides[get_relogio] = lambda: RelogioFake(datetime.now(UTC) + timedelta(hours=horas))
    r = await client.get("/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


async def test_delegado_nao_registra_ocorrencia_403_auditado(client, session):

    r = await client.post("/v1/ocorrencias", json=corpo_ocorrencia(), headers=await auth(client, "delegado"))
    assert r.status_code == 403
    assert r.json()["code"] == "auth.forbidden" and r.json()["extra"]["exigido"] == ["AGENTE"]
    negados = (await session.execute(select(RegistroAuditoriaModel).where(RegistroAuditoriaModel.operacao == "auth.acesso_negado"))).scalars().all()
    assert len(negados) == 1 and negados[0].quem == IDS["delegado"] and negados[0].entidade_id == "POST /v1/ocorrencias"


async def test_logins_sao_auditados(client, session):
    await token_de(client, "agente")
    await client.post("/v1/auth/login", json={"login": "agente", "senha": "errada"})
    ops = (await session.execute(select(RegistroAuditoriaModel.operacao).order_by(RegistroAuditoriaModel.quando))).scalars().all()
    assert ops == ["auth.login", "auth.login_negado"]


async def test_forca_bruta_no_login_bloqueia_com_429(client, session):
    for _ in range(5):
        r = await client.post("/v1/auth/login", json={"login": "delegado", "senha": "errada"})
        assert r.status_code == 401
    r = await client.post("/v1/auth/login", json={"login": "delegado", "senha": SENHA_PADRAO})
    assert r.status_code == 429
    assert r.json()["code"] == "auth.muitas_tentativas" and int(r.headers["Retry-After"]) > 0
    negados = (
        await session.execute(select(RegistroAuditoriaModel).where(RegistroAuditoriaModel.operacao == "auth.login_negado"))
    ).scalars().all()
    assert len(negados) == 5 and all(n.quem is None for n in negados)
    assert negados[0].dados_depois["usuario_alvo_id"] == str(IDS["delegado"])


async def test_token_de_usuario_desativado_deixa_de_valer(client, session_factory, usuarios):
    """O JWT vale horas: desativar o usuário precisa cortar o acesso na próxima requisição."""
    from sqlalchemy import update

    from infrastructure.database.models import UsuarioModel
    from tests.integration.helpers import auth

    headers = await auth(client, "agente")
    assert (await client.get("/v1/notificacoes/resumo", headers=headers)).status_code == 200
    async with session_factory() as s:
        await s.execute(update(UsuarioModel).where(UsuarioModel.id == usuarios["agente"]).values(ativo=False))
        await s.commit()
    assert (await client.get("/v1/notificacoes/resumo", headers=headers)).status_code == 401
