"""ListarCatalogoAuditoria: o catálogo da trilha vem das classes de evento."""
import pytest

from application.use_cases.auditoria.listar_catalogo_auditoria import ListarCatalogoAuditoria
from domain.auditoria import catalogo_eventos
from domain.shared.exceptions import AcessoNegadoError
from tests.fakes.atores import AGENTE, DELEGADO


async def test_lista_todas_as_acoes_com_a_entidade():
    acoes = await ListarCatalogoAuditoria().executar(DELEGADO)

    assert [(a.operacao, a.entidade) for a in acoes] == list(catalogo_eventos.catalogo())
    assert ("ocorrencia.validar", "Ocorrencia") in [(a.operacao, a.entidade) for a in acoes]


async def test_exige_permissao_de_consultar_auditoria():
    with pytest.raises(AcessoNegadoError):
        await ListarCatalogoAuditoria().executar(AGENTE)
