"""Issue #55: integração do gerador — persiste ocorrência simulada (TDD)."""
import pytest
from sqlalchemy import select

from infrastructure.database.models import OcorrenciaModel


@pytest.mark.asyncio
async def test_tick_persiste_ocorrencia_simulada(session_factory, monkeypatch):
    from scripts.seed import semear_usuarios

    monkeypatch.setattr("scripts.seed.AsyncSessionLocal", session_factory)
    await semear_usuarios()

    from infrastructure.di import montar_gerador
    from tests.fakes.portas_fake import RelogioFake
    from datetime import UTC, datetime

    gen = montar_gerador(session_factory, relogio=RelogioFake(datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)), semente=42)
    assert await gen.tick() == 1

    async with session_factory() as s:
        ocorrencias = (await s.execute(select(OcorrenciaModel).where(OcorrenciaModel.descricao.like("%[SIMULADO-DEMO]%")))).scalars().all()
        assert len(ocorrencias) == 1
        assert ocorrencias[0].status == "AGUARDANDO_REVISAO"


@pytest.mark.asyncio
async def test_app_boot_padrao_nao_inicia_gerador(monkeypatch):
    """Issue #55 ajuste 5: sem .env, o gerador nunca inicia nos testes/servidor padrão."""
    from infrastructure.config.settings import Settings

    s = Settings(_env_file=None)
    assert s.gerador_ocorrencias_ligado is False

    monkeypatch.setattr("infrastructure.di.settings.gerador_ocorrencias_ligado", False, raising=False)
    from main import criar_app
    import infrastructure.di as di

    app = criar_app()
    assert app is not None
    assert di.gerador_ocorrencias.ligado is False
