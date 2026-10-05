"""ListarOcorrencias / ObterDetalheOcorrencia (RF01, LGPD)."""
from datetime import timedelta
from uuid import uuid4

import pytest

from application.ports.inbound.interface_consultar_ocorrencias import ListarOcorrenciasInput
from application.use_cases.ocorrencia.consultar_ocorrencias import ListarOcorrencias, ObterDetalheOcorrencia
from domain.ocorrencia.entity import OrigemOcorrencia
from domain.shared.exceptions import AcessoNegadoError, EntidadeNaoEncontradaError, ValorInvalidoError
from tests.fakes.atores import AGENTE, DELEGADO, OPERADOR, OUTRO_AGENTE
from tests.unit.use_cases.conftest import AGORA


async def test_lista_fila_ordenada_mais_antiga_primeiro(registrar, repositorio, relogio):
    o1 = await registrar()
    relogio.avancar(minutes=1)
    o2 = await registrar()
    pagina = await ListarOcorrencias(repositorio).executar(DELEGADO, ListarOcorrenciasInput(status=("AGUARDANDO_REVISAO",)))
    assert [i.ocorrencia_id for i in pagina.itens] == [o1.ocorrencia_id, o2.ocorrencia_id]
    assert pagina.total == 2


async def test_mais_recentes_primeiro_inverte_a_ordem_antes_de_paginar(registrar, repositorio, relogio):
    """"Minhas ocorrências": com mais itens que o limite, a página traz as MAIS NOVAS."""
    criadas = []
    for _ in range(3):
        criadas.append(await registrar())
        relogio.avancar(minutes=1)
    pagina = await ListarOcorrencias(repositorio).executar(AGENTE, ListarOcorrenciasInput(limit=2, mais_recentes_primeiro=True))
    assert [i.ocorrencia_id for i in pagina.itens] == [criadas[2].ocorrencia_id, criadas[1].ocorrencia_id]
    assert pagina.total == 3


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


# ------------------------------------------------- sugestão #1: filtros e busca
async def _listar(repositorio, ator=DELEGADO, **kw):
    return await ListarOcorrencias(repositorio).executar(ator, ListarOcorrenciasInput(**kw))


async def test_busca_por_natureza_protocolo_e_texto_ignora_maiusculas(registrar, repositorio):
    furto = await registrar(natureza="Furto", localizacao="Rua dos Andradas, 10")
    roubo = await registrar(natureza="Roubo a pedestre", descricao="Roubo de celular mediante grave ameaça.")
    assert [i.ocorrencia_id for i in (await _listar(repositorio, natureza="  rOuBo ")).itens] == [roubo.ocorrencia_id]
    assert [i.ocorrencia_id for i in (await _listar(repositorio, protocolo=furto.numero_protocolo.lower())).itens] == [furto.ocorrencia_id]
    assert (await _listar(repositorio, texto="CELULAR")).total == 1  # descrição
    assert (await _listar(repositorio, texto="andradas")).total == 1  # localização
    assert (await _listar(repositorio, texto="   ")).total == 2  # termo vazio = sem filtro


async def test_busca_por_periodo_do_fato(registrar, repositorio):
    antiga = await registrar(data_hora_fato=AGORA - timedelta(days=10))
    recente = await registrar(data_hora_fato=AGORA - timedelta(hours=1))
    pagina = await _listar(repositorio, data_fato_de=AGORA - timedelta(days=1))
    assert [i.ocorrencia_id for i in pagina.itens] == [recente.ocorrencia_id]
    pagina = await _listar(repositorio, data_fato_ate=(AGORA - timedelta(days=5)).replace(tzinfo=None))  # sem fuso = UTC
    assert [i.ocorrencia_id for i in pagina.itens] == [antiga.ocorrencia_id]


async def test_periodo_invertido_e_origem_invalida(repositorio):
    with pytest.raises(ValorInvalidoError) as exc:
        await _listar(repositorio, data_fato_de=AGORA, data_fato_ate=AGORA - timedelta(days=1))
    assert exc.value.chave == "ocorrencia.periodo_invalido"
    with pytest.raises(ValorInvalidoError) as exc:
        await _listar(repositorio, origem="XPTO")
    assert exc.value.chave == "ocorrencia.origem_invalida"


async def test_busca_por_origem(registrar, repositorio):
    o = await registrar()
    assert (await _listar(repositorio, origem="policial")).total == 1
    assert (await _listar(repositorio, origem="PUBLICA")).total == 0
    repositorio._store[o.ocorrencia_id].origem = OrigemOcorrencia.PUBLICA
    assert (await _listar(repositorio, origem="PUBLICA")).total == 1


async def test_filtros_nao_furam_o_rbac_do_agente(registrar, repositorio):
    await registrar(OUTRO_AGENTE, natureza="Roubo")
    assert (await _listar(repositorio, AGENTE, natureza="Roubo")).total == 0
