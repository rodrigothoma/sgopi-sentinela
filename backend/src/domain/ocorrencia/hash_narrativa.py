"""
Hash de integridade do documento oficial da ocorrência (DEC-09 / RF08).

Cada versão do algoritmo é uma estratégia de canonicalização (ocorrência → texto) e fica
registrada em ``CANONICALIZADORES``. A versão usada na emissão é gravada em ``hash_versao``,
então um algoritmo novo entra como nova versão sem invalidar documentos já emitidos.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from typing import TYPE_CHECKING

from domain.shared.exceptions import ValorInvalidoError

if TYPE_CHECKING:
    from domain.ocorrencia.entity import Ocorrencia

VERSAO_HASH_LEGADA = 1
VERSAO_HASH_ATUAL = 2


def _conteudo_v1(oc: Ocorrencia) -> str:
    """Legado: separadores sem escape permitiam colisão deslocando texto entre campos (N5)."""
    partes = [oc.natureza, oc.descricao, oc.localizacao, oc.data_hora_fato.isoformat()]
    partes += sorted(f"{e.tipo.value}|{e.nome}|{e.documento or ''}" for e in oc.envolvidos)
    partes += sorted(f"{t.artigo}|{t.descricao}" for t in oc.tipificacoes)
    return "\n".join(partes)


def _conteudo_v2(oc: Ocorrencia) -> str:
    """JSON canônico (campos nomeados, chaves ordenadas): sem ambiguidade entre campos.

    Inclui o SHA-256 das evidências, que não mudam após a validação. Itens apreendidos ficam
    de fora: a custódia continua sendo movimentada depois da emissão do documento.
    """
    documento = {
        "versao": 2,
        "natureza": oc.natureza,
        "descricao": oc.descricao,
        "localizacao": oc.localizacao,
        "data_hora_fato": oc.data_hora_fato.isoformat(),
        "envolvidos": sorted([e.tipo.value, e.nome, e.documento or ""] for e in oc.envolvidos),
        "tipificacoes": sorted([t.artigo, t.descricao] for t in oc.tipificacoes),
        "evidencias": sorted(e.hash_sha256 for e in oc.evidencias),
    }
    return json.dumps(documento, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


CANONICALIZADORES: dict[int, Callable[[Ocorrencia], str]] = {
    VERSAO_HASH_LEGADA: _conteudo_v1,
    VERSAO_HASH_ATUAL: _conteudo_v2,
}


def calcular_hash(oc: Ocorrencia, versao: int) -> str:
    canonicalizar = CANONICALIZADORES.get(versao)
    if canonicalizar is None:
        raise ValorInvalidoError(f"Versão de hash desconhecida: {versao}", chave="documento.versao_hash_desconhecida")
    return hashlib.sha256(canonicalizar(oc).encode("utf-8")).hexdigest()
