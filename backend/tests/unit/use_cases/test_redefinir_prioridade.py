"""Sugestão #7: o Delegado redefine a prioridade (auditada) e a fila ordena pela gravidade."""
import pytest

from application.ports.inbound.interface_consultar_ocorrencias import ListarOcorrenciasInput
from application.ports.inbound.interface_redefinir_prioridade import RedefinirPrioridadeInput
from application.use_cases.ocorrencia.consultar_ocorrencias import ListarOcorrencias
from application.use_cases.ocorrencia.redefinir_prioridade import RedefinirPrioridade
from domain.shared.exceptions import AcessoNegadoError, CampoObrigatorioError
from tests.fakes.atores import AGENTE, DELEGADO, OPERADOR

JUSTIFICATIVA = "Há relato de arma de fogo no local."


async def test_delegado_redefine_audita_e_publica(registrar, deps, auditoria, publicador):
    o = await registrar()
    det = await RedefinirPrioridade(*deps).executar(DELEGADO, RedefinirPrioridadeInput(o.ocorrencia_id, "urgente", JUSTIFICATIVA))
    assert det.prioridade == "URGENTE"
    registro = auditoria.registros[-1]
    assert registro.operacao == "ocorrencia.redefinir_prioridade"
    assert registro.dados_antes == {"prioridade": "MEDIA", "versao": 1}
    assert registro.dados_depois == {"prioridade": "URGENTE", "versao": 2, "justificativa": JUSTIFICATIVA}
    assert publicador.tipos() == ["OcorrenciaPrioridadeAlterada"]
    assert publicador.eventos[0].dados["prioridade"] == "URGENTE"


@pytest.mark.parametrize("ator", [AGENTE, OPERADOR])
async def test_somente_delegado(registrar, deps, ator):
    o = await registrar()
    with pytest.raises(AcessoNegadoError):
        await RedefinirPrioridade(*deps).executar(ator, RedefinirPrioridadeInput(o.ocorrencia_id, "ALTA", JUSTIFICATIVA))


async def test_prioridade_vazia(registrar, deps):
    o = await registrar()
    with pytest.raises(CampoObrigatorioError):
        await RedefinirPrioridade(*deps).executar(DELEGADO, RedefinirPrioridadeInput(o.ocorrencia_id, " ", JUSTIFICATIVA))


async def test_registro_sugere_e_fila_ordena_por_gravidade(registrar, repositorio, relogio):
    furto = await registrar(natureza="Furto")
    relogio.avancar(minutes=1)
    roubo = await registrar(natureza="Roubo")
    relogio.avancar(minutes=1)
    perda = await registrar(natureza="Perda de documento", prioridade="BAIXA")
    relogio.avancar(minutes=1)
    outro_roubo = await registrar(natureza="Roubo")
    assert (roubo.prioridade, furto.prioridade, perda.prioridade) == ("ALTA", "MEDIA", "BAIXA")
    pagina = await ListarOcorrencias(repositorio).executar(DELEGADO, ListarOcorrenciasInput(ordenar_por_prioridade=True))
    esperado = [roubo.ocorrencia_id, outro_roubo.ocorrencia_id, furto.ocorrencia_id, perda.ocorrencia_id]
    assert [i.ocorrencia_id for i in pagina.itens] == esperado
