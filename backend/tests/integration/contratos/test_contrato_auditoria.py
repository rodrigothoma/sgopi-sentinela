"""Contrato de PortaAuditoria: período, paginação e contagem iguais na fake e no SQLAlchemy."""
from datetime import UTC, datetime, timedelta

import pytest

from adapters.outbound.persistence.auditoria_sqlalchemy import AuditoriaSQLAlchemy
from domain.auditoria.contexto import ContextoAuditoria
from domain.usuario.auditoria import LoginNegado
from tests.fakes.portas_fake import AuditoriaFake
from tests.integration.contratos.conftest import IMPLEMENTACOES, sessoes_fake, sessoes_sqlalchemy

INICIO = datetime(2026, 11, 10, 12, 0, tzinfo=UTC)


@pytest.fixture
def sessoes_auditoria(request, implementacao):
    if implementacao == "fake":
        return sessoes_fake(AuditoriaFake())
    return sessoes_sqlalchemy(request.getfixturevalue("session_factory"), AuditoriaSQLAlchemy)


async def _gravar_um_por_dia(sessoes, dias: int) -> None:
    async with sessoes() as s:
        for d in range(dias):
            evento = LoginNegado(login=f"login{d}", usuario_alvo_id=None, motivo="senha_invalida")
            await s.repo.registrar(evento, ContextoAuditoria(quem=None, quando=INICIO + timedelta(days=d)))
        await s.commit()


@IMPLEMENTACOES
async def test_periodo_e_inclusivo_no_inicio_e_exclusivo_no_fim(sessoes_auditoria):
    await _gravar_um_por_dia(sessoes_auditoria, 5)  # dias 10 a 14

    async with sessoes_auditoria() as s:
        itens = await s.repo.listar(de=INICIO + timedelta(days=1), ate=INICIO + timedelta(days=3))
        total = await s.repo.contar(de=INICIO + timedelta(days=1), ate=INICIO + timedelta(days=3))

    assert [r.entidade_id for r in itens] == ["login2", "login1"]  # mais recente primeiro
    assert total == 2


@IMPLEMENTACOES
async def test_offset_pagina_a_partir_do_mais_recente(sessoes_auditoria):
    await _gravar_um_por_dia(sessoes_auditoria, 5)

    async with sessoes_auditoria() as s:
        primeira = await s.repo.listar(limit=2, offset=0)
        segunda = await s.repo.listar(limit=2, offset=2)
        ultima = await s.repo.listar(limit=2, offset=4)
        total = await s.repo.contar()

    assert [r.entidade_id for r in primeira] == ["login4", "login3"]
    assert [r.entidade_id for r in segunda] == ["login2", "login1"]
    assert [r.entidade_id for r in ultima] == ["login0"]
    assert total == 5


@IMPLEMENTACOES
async def test_contar_respeita_os_mesmos_filtros_de_listar(sessoes_auditoria):
    await _gravar_um_por_dia(sessoes_auditoria, 3)

    async with sessoes_auditoria() as s:
        assert await s.repo.contar(operacao="auth.login_negado") == 3
        assert await s.repo.contar(operacao="ocorrencia.validar") == 0
        assert await s.repo.contar(entidade_id="login1") == 1
