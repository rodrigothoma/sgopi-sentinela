"""Caso de uso: CalcularIndicadores (sugestão #11) — somente leitura, agregação delegada ao banco."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_indicadores import (
    ContagemOutput,
    DuracaoOutput,
    IndicadoresInput,
    IndicadoresOutput,
    InterfaceCalcularIndicadores,
)
from application.ports.outbound.consulta_indicadores import ConsultaIndicadores, MediaDuracao
from application.ports.outbound.relogio import Relogio
from domain.ocorrencia.status import StatusOcorrencia
from domain.shared.exceptions import ValorInvalidoError
from domain.usuario.entity import Papel

PAPEIS_INDICADORES = (Papel.DELEGADO, Papel.SUPERVISOR, Papel.OPERADOR_CENTRAL)
PERIODO_PADRAO = timedelta(days=30)
PERIODO_MAXIMO = timedelta(days=366)
HORAS_DO_DIA = 24
MAXIMO_NATUREZAS = 10
CHAVE_OUTRAS_NATUREZAS = "OUTRAS"
DECISOES = (StatusOcorrencia.VALIDADA, StatusOcorrencia.EM_CORRECAO, StatusOcorrencia.REJEITADA)


def _fuso(nome: str) -> ZoneInfo:
    try:
        return ZoneInfo(nome)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ValorInvalidoError(f"Fuso horário inválido: {nome}", chave="indicadores.fuso_invalido") from exc


def _periodo(input_dto: IndicadoresInput, agora: datetime) -> tuple[datetime, datetime]:
    ate = input_dto.ate or agora
    de = input_dto.de or ate - PERIODO_PADRAO
    if de.tzinfo is None or ate.tzinfo is None:
        raise ValorInvalidoError("As datas do período devem informar o fuso.", chave="indicadores.periodo_sem_fuso")
    if de > ate or ate - de > PERIODO_MAXIMO:
        raise ValorInvalidoError(
            "Período inválido: início após o fim ou maior que 366 dias.", chave="indicadores.periodo_invalido"
        )
    return de, ate


def para_horas_locais(por_hora_utc: dict[int, int], fuso: ZoneInfo, referencia: datetime) -> tuple[int, ...]:
    """Desloca as 24 faixas UTC para a hora local pelo deslocamento do fuso na data de referência."""
    deslocamento = referencia.astimezone(fuso).utcoffset() or timedelta()
    horas = int(deslocamento.total_seconds() // 3600)
    locais = [0] * HORAS_DO_DIA
    for hora_utc, total in por_hora_utc.items():
        locais[(hora_utc + horas) % HORAS_DO_DIA] += total
    return tuple(locais)


def _naturezas(contagem: dict[str, int]) -> tuple[ContagemOutput, ...]:
    ordenadas = sorted(contagem.items(), key=lambda kv: (-kv[1], kv[0]))
    principais = [ContagemOutput(chave, total) for chave, total in ordenadas[:MAXIMO_NATUREZAS]]
    resto = sum(total for _, total in ordenadas[MAXIMO_NATUREZAS:])
    return tuple(principais + ([ContagemOutput(CHAVE_OUTRAS_NATUREZAS, resto)] if resto else []))


def _contagens(contagem: dict[str, int]) -> tuple[ContagemOutput, ...]:
    return tuple(ContagemOutput(chave, total) for chave, total in sorted(contagem.items()))


def _duracao(media: MediaDuracao) -> DuracaoOutput:
    return DuracaoOutput(media_segundos=media.segundos, amostras=media.amostras)


def _taxa(parte: int, total: int) -> float | None:
    return parte / total if total else None


class CalcularIndicadores(InterfaceCalcularIndicadores):
    def __init__(self, consulta: ConsultaIndicadores, relogio: Relogio) -> None:
        self._consulta = consulta
        self._relogio = relogio

    async def executar(self, ator: Ator, input_dto: IndicadoresInput) -> IndicadoresOutput:
        ator.exigir_papel(*PAPEIS_INDICADORES)
        fuso = _fuso(input_dto.fuso)
        de, ate = _periodo(input_dto, self._relogio.agora())
        c = self._consulta
        naturezas = await c.ocorrencias_por_natureza(de, ate)
        por_destino = await c.decisoes_do_delegado(de, ate)
        decisoes = {s.value: por_destino.get(s.value, 0) for s in DECISOES}
        total_decisoes = sum(decisoes.values())
        return IndicadoresOutput(
            de=de.isoformat(),
            ate=ate.isoformat(),
            fuso=input_dto.fuso,
            total_ocorrencias=sum(naturezas.values()),
            por_natureza=_naturezas(naturezas),
            por_origem=_contagens(await c.ocorrencias_por_origem(de, ate)),
            por_faixa_horaria=para_horas_locais(await c.ocorrencias_por_hora_utc(de, ate), fuso, ate),
            decisoes=tuple(ContagemOutput(chave, total) for chave, total in decisoes.items()),
            taxa_devolucao=_taxa(decisoes[StatusOcorrencia.EM_CORRECAO.value], total_decisoes),
            taxa_rejeicao=_taxa(decisoes[StatusOcorrencia.REJEITADA.value], total_decisoes),
            tempo_ate_decisao=_duracao(await c.tempo_ate_primeira_decisao(de, ate)),
            tempo_validacao_despacho=_duracao(await c.tempo_validacao_ate_despacho(de, ate)),
            tempo_despacho_encerramento=_duracao(await c.tempo_despacho_ate_encerramento(de, ate)),
            despachos_por_hora=para_horas_locais(await c.despachos_por_hora_utc(de, ate), fuso, ate),
            viaturas_por_situacao=_contagens(await c.viaturas_por_situacao()),
        )
