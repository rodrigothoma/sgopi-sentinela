"""Casos de uso de frota e telemetria + simulador com fakes (RF15, RF16)."""
from contextlib import asynccontextmanager
from datetime import timedelta

import pytest

from adapters.inbound.simulador.simulador_telemetria import SimuladorTelemetria
from application.ports.inbound.interface_gerir_viaturas import AlterarSituacaoInput, CadastrarViaturaInput, RegistrarPosicaoInput
from application.use_cases.viatura.gerir_viaturas import AlterarSituacaoViatura, CadastrarViatura, ListarViaturas
from application.use_cases.viatura.registrar_posicao_viatura import RegistrarPosicaoViatura
from domain.shared.exceptions import AcessoNegadoError, ConflitoError, EntidadeNaoEncontradaError, TransicaoInvalidaError, ValorInvalidoError
from domain.shared.geo import calcular_distancia_km
from tests.fakes.atores import AGENTE, DELEGADO, OPERADOR
from tests.fakes.portas_fake import AuditoriaFake, PublicadorEventosFake, RelogioFake, UnidadeDeTrabalhoFake
from tests.fakes.repositorio_viatura_fake import RepositorioViaturaFake
from tests.unit.use_cases.conftest import AGORA


@pytest.fixture
def repo():
    return RepositorioViaturaFake()


@pytest.fixture
def relogio():
    return RelogioFake(AGORA)


@pytest.fixture
def publicador():
    return PublicadorEventosFake()


@pytest.fixture
def auditoria():
    return AuditoriaFake()


@pytest.fixture
def cadastrar(repo, relogio, auditoria):
    return CadastrarViatura(repo, UnidadeDeTrabalhoFake(), relogio, auditoria, 60)


@pytest.fixture
def registrar_posicao(repo, relogio, publicador):
    return RegistrarPosicaoViatura(repo, UnidadeDeTrabalhoFake(), relogio, publicador, 60)


async def test_cadastrar_e_listar(cadastrar, repo, relogio, auditoria):
    v = await cadastrar.executar(OPERADOR, CadastrarViaturaInput("vtr-01", "IAB1A23"))
    assert v.prefixo == "VTR-01" and v.sinal == "SEM_POSICAO" and auditoria.operacoes() == ["viatura.cadastrar"]
    lista = await ListarViaturas(repo, relogio, 60).executar(DELEGADO)
    assert [x.prefixo for x in lista] == ["VTR-01"]


async def test_cadastrar_duplicado_409(cadastrar):
    await cadastrar.executar(OPERADOR, CadastrarViaturaInput("VTR-01", "IAB1A23"))
    with pytest.raises(ConflitoError) as e:
        await cadastrar.executar(OPERADOR, CadastrarViaturaInput("vtr-01", "ZZZ9999"))
    assert e.value.chave == "viatura.prefixo_duplicado"
    with pytest.raises(ConflitoError) as e:
        await cadastrar.executar(OPERADOR, CadastrarViaturaInput("VTR-02", "iab1a23"))
    assert e.value.chave == "viatura.placa_duplicada"


async def test_somente_operador_gere_frota(cadastrar):
    for ator in (AGENTE, DELEGADO):
        with pytest.raises(AcessoNegadoError):
            await cadastrar.executar(ator, CadastrarViaturaInput("VTR-01", "IAB1A23"))


async def test_alterar_situacao_manual(cadastrar, repo, relogio, auditoria, publicador):
    v = await cadastrar.executar(OPERADOR, CadastrarViaturaInput("VTR-01", "IAB1A23"))
    uc = AlterarSituacaoViatura(repo, UnidadeDeTrabalhoFake(), relogio, auditoria, publicador, 60)
    out = await uc.executar(OPERADOR, AlterarSituacaoInput(v.id, "INDISPONIVEL"))
    assert out.situacao == "INDISPONIVEL" and publicador.tipos() == ["ViaturaSituacaoAlterada"]
    with pytest.raises(ValorInvalidoError):
        await uc.executar(OPERADOR, AlterarSituacaoInput(v.id, "EM_DESLOCAMENTO"))
    with pytest.raises(TransicaoInvalidaError):
        await uc.executar(OPERADOR, AlterarSituacaoInput(v.id, "INDISPONIVEL"))
    with pytest.raises(EntidadeNaoEncontradaError):
        await uc.executar(OPERADOR, AlterarSituacaoInput(__import__("uuid").uuid4(), "DISPONIVEL"))


async def test_registrar_posicao_publica_evento_e_rejeita_invalida(cadastrar, registrar_posicao, publicador, repo):
    v = await cadastrar.executar(OPERADOR, CadastrarViaturaInput("VTR-01", "IAB1A23"))
    out = await registrar_posicao.executar(RegistrarPosicaoInput(v.id, -29.78, -55.79, AGORA - timedelta(seconds=5)))
    assert out.sinal == "OK" and out.latitude == -29.78
    assert publicador.tipos() == ["PosicaoAtualizada"] and publicador.eventos[0].dados["prefixo"] == "VTR-01"
    with pytest.raises(ValorInvalidoError):
        await registrar_posicao.executar(RegistrarPosicaoInput(v.id, 0, 0, AGORA - timedelta(minutes=5)))
    assert (await repo.buscar_por_id(v.id)).ultima_posicao.coordenada.latitude == -29.78
    assert len(publicador.eventos) == 1


async def test_simulador_tick_move_frota_dentro_do_raio(cadastrar, repo, relogio, publicador, registrar_posicao):
    ids = [(await cadastrar.executar(OPERADOR, CadastrarViaturaInput(f"VTR-0{i}", f"AAA000{i}"))).id for i in range(1, 4)]
    indisponivel = await cadastrar.executar(OPERADOR, CadastrarViaturaInput("VTR-09", "ZZZ9999"))
    v = await repo.buscar_por_id(indisponivel.id)
    v.marcar_indisponivel(AGORA)
    await repo.salvar(v)

    @asynccontextmanager
    async def contexto():
        yield repo, registrar_posicao

    sim = SimuladorTelemetria(contexto, relogio, intervalo_segundos=0.01, raio_metros=100, semente=42)
    assert await sim.tick() == 3
    primeiras = {i: (await repo.buscar_por_id(i)).ultima_posicao.coordenada for i in ids}
    assert (await repo.buscar_por_id(indisponivel.id)).ultima_posicao is None
    relogio.avancar(seconds=1)
    assert await sim.tick() == 3
    for i in ids:
        nova = (await repo.buscar_por_id(i)).ultima_posicao.coordenada
        assert calcular_distancia_km(primeiras[i], nova) * 1000 <= 100.5
    assert sim.status()["ticks"] == 2 and sim.posicoes_emitidas == 6
    assert publicador.tipos().count("PosicaoAtualizada") == 6


async def test_simulador_liga_e_desliga(repo, relogio, registrar_posicao):
    @asynccontextmanager
    async def contexto():
        yield repo, registrar_posicao

    sim = SimuladorTelemetria(contexto, relogio, intervalo_segundos=0.01)
    assert not sim.ligado
    sim.ligar()
    sim.ligar()  # idempotente
    assert sim.ligado
    import asyncio

    await asyncio.sleep(0.05)
    await sim.desligar()
    assert not sim.ligado and sim.ticks >= 2
