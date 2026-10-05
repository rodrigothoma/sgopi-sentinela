"""Adapter de entrada: /v1/indicadores — painel de KPIs operacionais (sugestão #11)."""
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from adapters.inbound.http.deps import exigir_papel
from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_indicadores import (
    FUSO_PADRAO,
    ContagemOutput,
    DuracaoOutput,
    IndicadoresInput,
    InterfaceCalcularIndicadores,
)
from domain.usuario.entity import Papel
from infrastructure.di import get_calcular_indicadores

router = APIRouter(prefix="/v1/indicadores", tags=["indicadores"])


class ContagemSchema(BaseModel):
    chave: str
    total: int


class DuracaoSchema(BaseModel):
    media_segundos: float | None
    amostras: int


class IndicadoresSchema(BaseModel):
    de: str
    ate: str
    fuso: str
    total_ocorrencias: int
    por_natureza: list[ContagemSchema]
    por_origem: list[ContagemSchema]
    por_faixa_horaria: list[int]
    decisoes: list[ContagemSchema]
    taxa_devolucao: float | None
    taxa_rejeicao: float | None
    tempo_ate_decisao: DuracaoSchema
    tempo_validacao_despacho: DuracaoSchema
    tempo_despacho_encerramento: DuracaoSchema
    despachos_por_hora: list[int]
    viaturas_por_situacao: list[ContagemSchema]


def _contagens(itens: tuple[ContagemOutput, ...]) -> list[ContagemSchema]:
    return [ContagemSchema(chave=i.chave, total=i.total) for i in itens]


def _duracao(d: DuracaoOutput) -> DuracaoSchema:
    return DuracaoSchema(media_segundos=d.media_segundos, amostras=d.amostras)


@router.get("", response_model=IndicadoresSchema)
async def obter_indicadores(
    de: datetime | None = Query(default=None),
    ate: datetime | None = Query(default=None),
    fuso: str = Query(default=FUSO_PADRAO, max_length=64),
    ator: Ator = Depends(exigir_papel(Papel.DELEGADO, Papel.SUPERVISOR, Papel.OPERADOR_CENTRAL)),
    use_case: InterfaceCalcularIndicadores = Depends(get_calcular_indicadores),
) -> IndicadoresSchema:
    """KPIs de RF01 (volume), RF04 (triagem) e RF02 (despacho) no período (padrão: últimos 30 dias)."""
    out = await use_case.executar(ator, IndicadoresInput(de=de, ate=ate, fuso=fuso))
    return IndicadoresSchema(
        de=out.de,
        ate=out.ate,
        fuso=out.fuso,
        total_ocorrencias=out.total_ocorrencias,
        por_natureza=_contagens(out.por_natureza),
        por_origem=_contagens(out.por_origem),
        por_faixa_horaria=list(out.por_faixa_horaria),
        decisoes=_contagens(out.decisoes),
        taxa_devolucao=out.taxa_devolucao,
        taxa_rejeicao=out.taxa_rejeicao,
        tempo_ate_decisao=_duracao(out.tempo_ate_decisao),
        tempo_validacao_despacho=_duracao(out.tempo_validacao_despacho),
        tempo_despacho_encerramento=_duracao(out.tempo_despacho_encerramento),
        despachos_por_hora=list(out.despachos_por_hora),
        viaturas_por_situacao=_contagens(out.viaturas_por_situacao),
    )
