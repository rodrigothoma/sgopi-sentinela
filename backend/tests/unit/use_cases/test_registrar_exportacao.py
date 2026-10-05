"""Sugestão #3: a exportação em massa é auditada e restrita a Delegado/Supervisor (RNF03)."""
from datetime import UTC, datetime
from uuid import UUID

import pytest

from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_registrar_exportacao import RecursoExportavel, RegistrarExportacaoInput
from application.use_cases.auditoria.registrar_exportacao import RegistrarExportacao
from domain.shared.exceptions import AcessoNegadoError
from domain.usuario.entity import Papel
from tests.fakes.atores import AGENTE, DELEGADO, OPERADOR

SUPERVISOR = Ator(id=UUID("00000000-0000-0000-0000-000000000005"), login="supervisor", papel=Papel.SUPERVISOR, ip="10.0.0.9")


async def test_registra_quem_o_que_filtros_e_total(auditoria, uow, relogio):
    filtros = {
        "status": ("VALIDADA",),
        "natureza": "Furto",
        "quem": UUID("00000000-0000-0000-0000-000000000001"),
        "data_fato_de": datetime(2026, 9, 1, tzinfo=UTC),
        "texto": None,
        "protocolo": "",
        "somente_minhas": False,
    }
    await RegistrarExportacao(auditoria, uow, relogio).executar(
        SUPERVISOR, RegistrarExportacaoInput(RecursoExportavel.OCORRENCIAS, "csv", 42, filtros)
    )
    [registro] = auditoria.registros
    assert registro.operacao == "ocorrencias.exportar" and registro.entidade == "Exportacao"
    assert registro.quem == SUPERVISOR.id and registro.ip == "10.0.0.9" and registro.quando == relogio.agora()
    assert registro.dados_depois == {
        "formato": "csv",
        "total_linhas": 42,
        "filtros": {
            "status": ["VALIDADA"],
            "natureza": "Furto",
            "quem": "00000000-0000-0000-0000-000000000001",
            "data_fato_de": "2026-09-01 00:00:00+00:00",
            "somente_minhas": False,
        },
    }
    assert uow.commits == 1


@pytest.mark.parametrize("ator", [AGENTE, OPERADOR])
async def test_somente_delegado_ou_supervisor_exporta(auditoria, uow, relogio, ator):
    with pytest.raises(AcessoNegadoError):
        await RegistrarExportacao(auditoria, uow, relogio).executar(
            ator, RegistrarExportacaoInput(RecursoExportavel.AUDITORIA, "csv", 0)
        )
    assert auditoria.registros == [] and uow.commits == 0


async def test_delegado_exporta_auditoria(auditoria, uow, relogio):
    await RegistrarExportacao(auditoria, uow, relogio).executar(DELEGADO, RegistrarExportacaoInput(RecursoExportavel.AUDITORIA, "csv", 3))
    assert auditoria.operacoes() == ["auditoria.exportar"]
