"""Issue #55: GeradorOcorrencias — driving adapter TDD (um teste por vez)."""
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from uuid import uuid4

from adapters.inbound.simulador.catalogo_demo import MARCA_SIMULADO
from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_registrar_ocorrencia_policial import RegistrarOcorrenciaOutput
from domain.usuario.entity import Papel


class _RelogioFixo:
    def agora(self):
        return datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)


class _RegistrarFake:
    def __init__(self):
        self.chamadas = []

    async def executar(self, ator, input_dto):
        self.chamadas.append((ator, input_dto))
        return RegistrarOcorrenciaOutput(
            ocorrencia_id=uuid4(), numero_protocolo="SGOPI-2026-000099", status="AGUARDANDO_REVISAO", criada_em="2026-01-01T12:00:00+00:00"
        )


def _fabrica(ator, registrar):
    @asynccontextmanager
    async def _ctx():
        yield ator, registrar

    return _ctx


async def test_tick_gera_ocorrencia_com_marca_e_autor():
    from adapters.inbound.simulador.gerador_ocorrencias import GeradorOcorrencias

    ator = Ator(id=uuid4(), login="simulador-demo", papel=Papel.AGENTE)
    registrar = _RegistrarFake()
    gen = GeradorOcorrencias(_fabrica(ator, registrar), _RelogioFixo(), intervalo_segundos=120.0, semente=42)

    assert await gen.tick() == 1

    ator_usado, input_usado = registrar.chamadas[0]
    assert ator_usado.login == "simulador-demo"
    assert ator_usado.papel == Papel.AGENTE
    assert MARCA_SIMULADO in input_usado.descricao
    assert input_usado.natureza
    assert len(input_usado.envolvidos) == 1


async def test_sorteio_deterministico_com_semente():
    from adapters.inbound.simulador.gerador_ocorrencias import GeradorOcorrencias

    async def _gerar(semente):
        ator = Ator(id=uuid4(), login="simulador-demo", papel=Papel.AGENTE)
        registrar = _RegistrarFake()
        gen = GeradorOcorrencias(_fabrica(ator, registrar), _RelogioFixo(), intervalo_segundos=120.0, semente=semente)
        await gen.tick()
        return registrar.chamadas[0][1]

    a = await _gerar(7)
    b = await _gerar(7)
    assert (a.natureza, a.descricao, a.localizacao) == (b.natureza, b.descricao, b.localizacao)


async def test_erro_de_registro_nao_derruba_loop():
    from adapters.inbound.simulador.gerador_ocorrencias import GeradorOcorrencias

    class _Falha:
        async def executar(self, ator, input_dto):
            raise RuntimeError("banco fora do ar")

    ator = Ator(id=uuid4(), login="simulador-demo", papel=Papel.AGENTE)
    gen = GeradorOcorrencias(_fabrica(ator, _Falha()), _RelogioFixo(), intervalo_segundos=120.0, semente=1)
    assert await gen.tick() == 0
    assert gen.ticks == 1 and gen.geradas == 0


async def test_sem_ator_nao_inicia_e_tick_retorna_zero(caplog):
    from adapters.inbound.simulador.gerador_ocorrencias import GeradorOcorrencias

    registrar = _RegistrarFake()
    gen = GeradorOcorrencias(_fabrica(None, registrar), _RelogioFixo(), intervalo_segundos=120.0, semente=1)
    assert await gen.ligar() is False
    assert gen.ligado is False
    assert await gen.tick() == 0
    assert registrar.chamadas == []
    assert "rode o seed" in caplog.text
