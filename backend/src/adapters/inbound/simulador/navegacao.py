"""Navegação pura do simulador com destino (issue #54, RF02).

Sem banco, sem rede, sem I/O: decide a próxima posição ao longo de uma rota
(lista de ``Coordenada``) respeitando o passo máximo e o raio de chegada.
O destino da navegação é o parâmetro ``destino`` (último ponto da rota).
"""
from __future__ import annotations

from dataclasses import dataclass

from domain.shared.geo import Coordenada


@dataclass(frozen=True)
class ResultadoAvanco:
    nova_posicao: Coordenada
    indice_rota: int
    chegou: bool


def avancar_na_rota(
    atual: Coordenada,
    destino: Coordenada,
    rota: list[Coordenada],
    indice: int = 0,
    passo_max_metros: float = 300.0,
    raio_chegada_metros: float = 50.0,
) -> ResultadoAvanco:
    """Avança de ``atual`` em direção a ``destino`` ao longo de ``rota``.

    Chegada usa ``<`` estrito: chegou quando a distância é **menor** que o raio.
    Sem informação de rota (vazia ou com menos de 2 pontos), mantém a posição.
    Com rota, consome o passo segmento a segmento (``passo = min(passo_max,
    restante)``) e nunca ultrapassa o destino; a chegada só é declarada no
    fim da rota, para a viatura não "pular" para o jitter no meio do caminho.
    """
    if atual == destino:
        return ResultadoAvanco(nova_posicao=destino, indice_rota=max(len(rota) - 1, 0), chegou=True)
    if len(rota) < 2:
        distancia_metros = atual.distancia_km(destino) * 1000.0
        return ResultadoAvanco(
            nova_posicao=atual, indice_rota=indice, chegou=distancia_metros < raio_chegada_metros
        )
    i = max(0, min(indice, len(rota) - 2))
    ponto = atual
    restante = passo_max_metros
    while restante > 0 and i <= len(rota) - 2:
        alvo = rota[i + 1]
        distancia_metros = ponto.distancia_km(alvo) * 1000.0
        if distancia_metros <= restante:
            ponto = alvo
            restante -= distancia_metros
            i += 1
        else:
            ponto = _interpolar(ponto, alvo, restante / distancia_metros)
            restante = 0
    fim_da_rota = i >= len(rota) - 1
    chegou = ponto == destino or (fim_da_rota and ponto.distancia_km(destino) * 1000.0 < raio_chegada_metros)
    return ResultadoAvanco(nova_posicao=ponto, indice_rota=min(i, len(rota) - 1), chegou=chegou)


def _interpolar(origem: Coordenada, alvo: Coordenada, fracao: float) -> Coordenada:
    """Interpola linearmente em graus decimais (mesma base do passeio aleatório)."""
    return Coordenada(
        round(origem.latitude + (alvo.latitude - origem.latitude) * fracao, 6),
        round(origem.longitude + (alvo.longitude - origem.longitude) * fracao, 6),
    )
