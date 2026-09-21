"""SugerirViaturasProximas, DespacharViatura, EncerrarOcorrencia com fakes (RF02, RNF03)."""
from datetime import timedelta

import pytest

from application.ports.inbound.interface_despachar_viatura import DespacharInput, EncerrarInput, ListarOrdensInput
from application.ports.inbound.interface_revisar_ocorrencia import DecisaoRevisaoInput
from application.use_cases.despacho.despachar_viatura import DespacharViatura, ListarOrdensDespacho, SugerirViaturasProximas
from application.use_cases.despacho.encerrar_ocorrencia import EncerrarOcorrencia
from application.use_cases.ocorrencia.revisar_ocorrencia import ValidarOcorrencia
from domain.shared.exceptions import AcessoNegadoError, CampoObrigatorioError, ConflitoError, TransicaoInvalidaError
from domain.shared.geo import Coordenada
from domain.viatura.entity import SituacaoViatura, Viatura
from tests.fakes.atores import AGENTE, DELEGADO, OPERADOR
from tests.fakes.despacho_fake import GeradorNumeroOrdemFake, RepositorioOrdemDespachoFake
from tests.fakes.repositorio_viatura_fake import RepositorioViaturaFake
from tests.unit.use_cases.conftest import AGORA


@pytest.fixture
def viaturas():
    return RepositorioViaturaFake()


@pytest.fixture
def ordens():
    return RepositorioOrdemDespachoFake()


@pytest.fixture
async def frota(viaturas):
    ids = {}
    for prefixo, lat, lon in [("VTR-01", -29.80, -55.80), ("VTR-02", -29.7833, -55.7919), ("VTR-03", -29.70, -55.70)]:
        v = Viatura(prefixo, f"P{prefixo[-2:]}0000")
        v.registrar_posicao(Coordenada(lat, lon), AGORA, AGORA, 60)
        await viaturas.salvar(v)
        ids[prefixo] = v.id
    sem_gps = Viatura("VTR-04", "P040000")
    await viaturas.salvar(sem_gps)
    ids["VTR-04"] = sem_gps.id
    return ids


@pytest.fixture
async def validada(registrar, deps):
    o = await registrar()
    await ValidarOcorrencia(*deps).executar(DELEGADO, DecisaoRevisaoInput(o.ocorrencia_id))
    return o.ocorrencia_id


@pytest.fixture
def despachar(repositorio, viaturas, ordens, uow, relogio, auditoria, publicador):
    return DespacharViatura(repositorio, viaturas, ordens, GeradorNumeroOrdemFake(), uow, relogio, auditoria, publicador)


@pytest.fixture
def encerrar(repositorio, viaturas, ordens, uow, relogio, auditoria, publicador):
    return EncerrarOcorrencia(repositorio, viaturas, ordens, uow, relogio, auditoria, publicador)


async def test_sugestoes_tres_mais_proximas(validada, frota, repositorio, viaturas, relogio):
    out = await SugerirViaturasProximas(repositorio, viaturas, relogio, 60, 3).executar(OPERADOR, validada)
    assert [s.viatura.prefixo for s in out.sugestoes] == ["VTR-02", "VTR-01", "VTR-03"]
    assert not out.sem_elegiveis and [v.prefixo for v in out.disponiveis_sem_posicao] == ["VTR-04"]


async def test_sugestoes_exigem_validada_e_operador(registrar, frota, repositorio, viaturas, relogio, validada):
    uc = SugerirViaturasProximas(repositorio, viaturas, relogio, 60, 3)
    nao_validada = await registrar()
    with pytest.raises(TransicaoInvalidaError):
        await uc.executar(OPERADOR, nao_validada.ocorrencia_id)
    with pytest.raises(AcessoNegadoError):
        await uc.executar(DELEGADO, validada)


async def test_sem_elegiveis_quando_sinal_velho(validada, frota, repositorio, viaturas, relogio):
    relogio.avancar(seconds=61)
    out = await SugerirViaturasProximas(repositorio, viaturas, relogio, 60, 3).executar(OPERADOR, validada)
    assert out.sem_elegiveis and len(out.disponiveis_sem_posicao) == 4


async def test_despacho_atomico_cria_ordem_e_muda_dois_agregados(validada, frota, despachar, repositorio, viaturas, ordens, auditoria, publicador, uow):
    ordem = await despachar.executar(OPERADOR, DespacharInput(validada, frota["VTR-02"], "Prioridade alta"))
    assert ordem.numero == "OD-2026-000001" and ordem.operador_id == OPERADOR.id and ordem.ativa
    assert ordem.criada_em == AGORA.isoformat() and ordem.observacoes == "Prioridade alta"
    assert (await repositorio.buscar_por_id(validada)).status.value == "EM_ATENDIMENTO"
    assert (await viaturas.buscar_por_id(frota["VTR-02"])).situacao == SituacaoViatura.EM_DESLOCAMENTO
    assert auditoria.operacoes()[-1] == "despacho.criar"
    assert publicador.tipos()[-3:] == ["OcorrenciaDespachada", "ViaturaSituacaoAlterada", "OrdemDeDespachoCriada"]
    listadas = await ListarOrdensDespacho(ordens).executar(OPERADOR, ListarOrdensInput(ocorrencia_id=validada, somente_ativas=True))
    assert [o.numero for o in listadas] == ["OD-2026-000001"]


async def test_despacho_manual_de_viatura_sem_gps_e_permitido(validada, frota, despachar):
    ordem = await despachar.executar(OPERADOR, DespacharInput(validada, frota["VTR-04"]))
    assert ordem.viatura_id == frota["VTR-04"]


async def test_despacho_de_viatura_nao_disponivel_409(validada, frota, despachar, registrar, deps, viaturas):
    await despachar.executar(OPERADOR, DespacharInput(validada, frota["VTR-02"]))
    outra = await registrar()
    await ValidarOcorrencia(*deps).executar(DELEGADO, DecisaoRevisaoInput(outra.ocorrencia_id))
    with pytest.raises(ConflitoError) as e:
        await despachar.executar(OPERADOR, DespacharInput(outra.ocorrencia_id, frota["VTR-02"]))
    assert e.value.chave == "despacho.viatura_indisponivel"


async def test_despacho_de_ocorrencia_nao_validada_422(registrar, frota, despachar):
    o = await registrar()
    with pytest.raises(TransicaoInvalidaError):
        await despachar.executar(OPERADOR, DespacharInput(o.ocorrencia_id, frota["VTR-01"]))


async def test_somente_operador_despacha(validada, frota, despachar):
    for ator in (AGENTE, DELEGADO):
        with pytest.raises(AcessoNegadoError):
            await despachar.executar(ator, DespacharInput(validada, frota["VTR-01"]))


async def test_falha_no_meio_faz_rollback(validada, frota, repositorio, viaturas, ordens, uow, relogio, auditoria, publicador):
    uc = DespacharViatura(repositorio, viaturas, ordens, GeradorNumeroOrdemFake(falhar=True), uow, relogio, auditoria, publicador)
    with pytest.raises(RuntimeError):
        await uc.executar(OPERADOR, DespacharInput(validada, frota["VTR-02"]))
    assert uow.rollbacks == 1 and await ordens.listar() == [] and publicador.tipos()[-1] == "OcorrenciaValidada"


async def test_encerrar_libera_viaturas_e_fecha_ordens(validada, frota, despachar, encerrar, repositorio, viaturas, ordens, relogio, publicador, auditoria):
    await despachar.executar(OPERADOR, DespacharInput(validada, frota["VTR-02"]))
    relogio.avancar(hours=1)
    with pytest.raises(CampoObrigatorioError):
        await encerrar.executar(OPERADOR, EncerrarInput(validada, "  "))
    det = await encerrar.executar(DELEGADO, EncerrarInput(validada, "Suspeito conduzido à delegacia."))
    assert det.status == "ENCERRADA" and det.desfecho == "Suspeito conduzido à delegacia."
    v = await viaturas.buscar_por_id(frota["VTR-02"])
    assert v.situacao == SituacaoViatura.DISPONIVEL and v.despachavel
    o = (await ordens.listar(validada))[0]
    assert not o.ativa and o.encerrada_em == AGORA + timedelta(hours=1)
    assert auditoria.registros[-1].dados_depois["viaturas_liberadas"] == ["VTR-02"]
    assert publicador.tipos()[-2:] == ["OcorrenciaEncerrada", "ViaturaSituacaoAlterada"]


async def test_encerrar_exige_em_atendimento(validada, encerrar):
    with pytest.raises(TransicaoInvalidaError):
        await encerrar.executar(OPERADOR, EncerrarInput(validada, "x"))


async def test_agente_nao_encerra(validada, encerrar):
    with pytest.raises(AcessoNegadoError):
        await encerrar.executar(AGENTE, EncerrarInput(validada, "x"))
