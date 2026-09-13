"""ListarOcorrencias / ObterDetalheOcorrencia (RF13, RNF10)."""
import pytest
from uuid import uuid4

from application.ports.inbound.interface_consultar_ocorrencias import ListarOcorrenciasInput
from application.use_cases.ocorrencia.consultar_ocorrencias import ListarOcorrencias, ObterDetalheOcorrencia
from domain.shared.exceptions import AcessoNegadoError, EntidadeNaoEncontradaError, ValorInvalidoError
from tests.fakes.atores import AGENTE, DELEGADO, OPERADOR, OUTRO_AGENTE


async def test_lista_fila_ordenada_mais_antiga_primeiro(registrar, repositorio, relogio):
    o1 = await registrar()
    relogio.avancar(minutes=1)
    o2 = await registrar()
    pagina = await ListarOcorrencias(repositorio).executar(DELEGADO, ListarOcorrenciasInput(status=("AGUARDANDO_REVISAO",)))
    assert [i.ocorrencia_id for i in pagina.itens] == [o1.ocorrencia_id, o2.ocorrencia_id]
    assert pagina.total == 2


async def test_agente_so_ve_as_proprias(registrar, repositorio):
    await registrar(AGENTE)
    await registrar(OUTRO_AGENTE)
    pagina = await ListarOcorrencias(repositorio).executar(AGENTE, ListarOcorrenciasInput())
    assert pagina.total == 1 and pagina.itens[0].agente_policial_id == AGENTE.id
    assert (await ListarOcorrencias(repositorio).executar(OPERADOR, ListarOcorrenciasInput())).total == 2


async def test_paginacao_e_limite_maximo(registrar, repositorio):
    for _ in range(3):
        await registrar()
    pagina = await ListarOcorrencias(repositorio).executar(DELEGADO, ListarOcorrenciasInput(limit=2, offset=2))
    assert len(pagina.itens) == 1 and pagina.total == 3
    pagina = await ListarOcorrencias(repositorio).executar(DELEGADO, ListarOcorrenciasInput(limit=9999))
    assert pagina.limit == 200


async def test_status_invalido(repositorio):
    with pytest.raises(ValorInvalidoError):
        await ListarOcorrencias(repositorio).executar(DELEGADO, ListarOcorrenciasInput(status=("XPTO",)))


async def test_detalhe_inclui_historico_e_mascara_cpf_para_operador(registrar, repositorio):
    o = await registrar()
    det = await ObterDetalheOcorrencia(repositorio).executar(OPERADOR, o.ocorrencia_id)
    assert det.envolvidos[0].documento == "***.***.789-**"
    assert len(det.historico_status) == 1 and det.historico_status[0].para == "AGUARDANDO_REVISAO"
    det_delegado = await ObterDetalheOcorrencia(repositorio).executar(DELEGADO, o.ocorrencia_id)
    assert det_delegado.envolvidos[0].documento == "123.456.789-09"
    det_autor = await ObterDetalheOcorrencia(repositorio).executar(AGENTE, o.ocorrencia_id)
    assert det_autor.envolvidos[0].documento == "123.456.789-09"


async def test_detalhe_404_e_403_para_outro_agente(registrar, repositorio):
    o = await registrar(AGENTE)
    with pytest.raises(EntidadeNaoEncontradaError):
        await ObterDetalheOcorrencia(repositorio).executar(DELEGADO, uuid4())
    with pytest.raises(AcessoNegadoError):
        await ObterDetalheOcorrencia(repositorio).executar(OUTRO_AGENTE, o.ocorrencia_id)
