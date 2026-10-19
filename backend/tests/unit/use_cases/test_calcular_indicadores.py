"""Sugestão #11: CalcularIndicadores — período, faixas horárias locais, taxas e agrupamento de naturezas."""
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from application.ports.inbound.interface_indicadores import IndicadoresInput
from application.ports.outbound.consulta_indicadores import ConsultaIndicadores, MediaDuracao
from application.use_cases.indicadores.calcular_indicadores import CalcularIndicadores, para_horas_locais
from domain.shared.exceptions import AcessoNegadoError, ValorInvalidoError
from tests.fakes.atores import AGENTE, DELEGADO, OPERADOR
from tests.fakes.portas_fake import RelogioFake

AGORA = datetime(2026, 10, 5, 12, tzinfo=UTC)


class ConsultaFake(ConsultaIndicadores):
    def __init__(self) -> None:
        self.periodos: list[tuple[datetime, datetime]] = []

    async def ocorrencias_por_natureza(self, de, ate):
        self.periodos.append((de, ate))
        return {f"N{i:02d}": 20 - i for i in range(12)}

    async def ocorrencias_por_origem(self, de, ate):
        return {"POLICIAL": 5, "PUBLICA": 2}

    async def ocorrencias_por_hora_utc(self, de, ate):
        return {0: 1, 2: 3, 15: 4}

    async def decisoes_do_delegado(self, de, ate):
        return {"VALIDADA": 6, "EM_CORRECAO": 3, "REJEITADA": 1}

    async def tempo_ate_primeira_decisao(self, de, ate):
        return MediaDuracao(600.0, 10)

    async def tempo_validacao_ate_despacho(self, de, ate):
        return MediaDuracao(None, 0)

    async def tempo_despacho_ate_encerramento(self, de, ate):
        return MediaDuracao(1800.0, 2)

    async def despachos_por_hora_utc(self, de, ate):
        return {3: 2}

    async def viaturas_por_situacao(self):
        return {"DISPONIVEL": 3, "OPERANDO": 1}


@pytest.fixture
def consulta():
    return ConsultaFake()


async def test_indicadores_completos_com_periodo_padrao(consulta):
    out = await CalcularIndicadores(consulta, RelogioFake(AGORA)).executar(DELEGADO, IndicadoresInput())
    assert consulta.periodos == [(AGORA - timedelta(days=30), AGORA)]
    assert out.total_ocorrencias == sum(20 - i for i in range(12))
    assert [c.chave for c in out.por_natureza][:3] == ["N00", "N01", "N02"]
    assert out.por_natureza[-1].chave == "OUTRAS" and out.por_natureza[-1].total == 9 + 10  # N10 e N11
    assert len(out.por_natureza) == 11
    assert [(c.chave, c.total) for c in out.decisoes] == [("VALIDADA", 6), ("EM_CORRECAO", 3), ("REJEITADA", 1)]
    assert out.taxa_devolucao == pytest.approx(0.3) and out.taxa_rejeicao == pytest.approx(0.1)
    assert out.tempo_ate_decisao.media_segundos == 600.0 and out.tempo_validacao_despacho.media_segundos is None
    # America/Sao_Paulo = UTC-3: 00h UTC → 21h, 02h → 23h, 15h → 12h; despacho 03h UTC → 00h
    assert out.por_faixa_horaria[21] == 1 and out.por_faixa_horaria[23] == 3 and out.por_faixa_horaria[12] == 4
    assert out.despachos_por_hora[0] == 2 and len(out.despachos_por_hora) == 24
    assert [(c.chave, c.total) for c in out.viaturas_por_situacao] == [("DISPONIVEL", 3), ("OPERANDO", 1)]


async def test_operador_acessa_e_agente_nao(consulta):
    await CalcularIndicadores(consulta, RelogioFake(AGORA)).executar(OPERADOR, IndicadoresInput())
    with pytest.raises(AcessoNegadoError):
        await CalcularIndicadores(consulta, RelogioFake(AGORA)).executar(AGENTE, IndicadoresInput())


@pytest.mark.parametrize(
    ("entrada", "chave"),
    [
        (IndicadoresInput(de=AGORA, ate=AGORA - timedelta(days=1)), "indicadores.periodo_invalido"),
        (IndicadoresInput(de=AGORA - timedelta(days=400), ate=AGORA), "indicadores.periodo_invalido"),
        (IndicadoresInput(de=datetime(2026, 10, 1), ate=AGORA), "indicadores.periodo_sem_fuso"),
        (IndicadoresInput(fuso="Marte/Olympus"), "indicadores.fuso_invalido"),
    ],
)
async def test_validacao_do_periodo_e_fuso(consulta, entrada, chave):
    with pytest.raises(ValorInvalidoError) as exc:
        await CalcularIndicadores(consulta, RelogioFake(AGORA)).executar(DELEGADO, entrada)
    assert exc.value.chave == chave


def test_horas_locais_com_fuso_positivo_e_sem_dados():
    assert para_horas_locais({23: 5}, ZoneInfo("Asia/Tokyo"), AGORA)[8] == 5  # UTC+9
    assert para_horas_locais({}, ZoneInfo("UTC"), AGORA) == (0,) * 24
