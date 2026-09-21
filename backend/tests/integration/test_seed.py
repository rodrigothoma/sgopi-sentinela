"""Testes do script reproduzível de seed (Issue #52 / LGPD)."""
import pytest
from sqlalchemy import select

from domain.ocorrencia.status import StatusOcorrencia
from infrastructure.database.models import OcorrenciaModel, UsuarioModel, ViaturaModel
from scripts.seed import main as run_seed


@pytest.mark.asyncio
async def test_seed_completo_e_idempotente(session_factory, monkeypatch):
    monkeypatch.setattr("scripts.seed.AsyncSessionLocal", session_factory)
    monkeypatch.setattr("scripts.seed_viaturas.AsyncSessionLocal", session_factory)
    monkeypatch.setattr("scripts.seed_ocorrencias.AsyncSessionLocal", session_factory)

    # 1. Primeira execução: deve semear usuários, viaturas e ocorrências
    await run_seed()

    async with session_factory() as s:
        usuarios = (await s.execute(select(UsuarioModel))).scalars().all()
        assert len(usuarios) >= 3
        logins = {u.login for u in usuarios}
        assert {"agente", "delegado", "operador"}.issubset(logins)

        viaturas = (await s.execute(select(ViaturaModel))).scalars().all()
        assert len(viaturas) == 5
        prefixos = {v.prefixo for v in viaturas}
        assert {"VTR-01", "VTR-02", "VTR-03", "VTR-04", "VTR-05"}.issubset(prefixos)
        for v in viaturas:
            assert v.latitude is not None
            assert v.longitude is not None

        ocorrencias = (await s.execute(select(OcorrenciaModel))).scalars().all()
        assert len(ocorrencias) == 5
        statuses = {o.status for o in ocorrencias}
        assert StatusOcorrencia.AGUARDANDO_REVISAO.value in statuses
        assert StatusOcorrencia.VALIDADA.value in statuses
        assert StatusOcorrencia.EM_ATENDIMENTO.value in statuses
        assert StatusOcorrencia.ENCERRADA.value in statuses
        assert StatusOcorrencia.EM_CORRECAO.value in statuses

    # 2. Segunda execução: deve ser 100% idempotente sem duplicar
    await run_seed()

    async with session_factory() as s:
        total_u = len((await s.execute(select(UsuarioModel))).scalars().all())
        total_v = len((await s.execute(select(ViaturaModel))).scalars().all())
        total_o = len((await s.execute(select(OcorrenciaModel))).scalars().all())
        assert total_u >= 3
        assert total_v == 5
        assert total_o == 5
