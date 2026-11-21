"""Toda chave de erro usada no backend tem mensagem em pt e en (senão a API devolve a chave crua)."""
import ast
import json
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[3] / "src"
LOCALES = SRC / "infrastructure" / "i18n" / "locales"
POSICAO_CHAVE = {"exigir_texto": 2, "interpretar_enum": 2}


def _nome_chamado(chamada: ast.Call) -> str:
    funcao = chamada.func
    return funcao.attr if isinstance(funcao, ast.Attribute) else getattr(funcao, "id", "")


def _chaves_da_chamada(chamada: ast.Call) -> list[str]:
    candidatos = [kw.value for kw in chamada.keywords if kw.arg == "chave"]
    posicao = POSICAO_CHAVE.get(_nome_chamado(chamada))
    if posicao is not None and len(chamada.args) > posicao:
        candidatos.append(chamada.args[posicao])
    return [c.value for c in candidatos if isinstance(c, ast.Constant) and isinstance(c.value, str)]


def _chaves_de_erro_usadas() -> set[str]:
    chaves: set[str] = set()
    for arquivo in SRC.rglob("*.py"):
        for no in ast.walk(ast.parse(arquivo.read_text(encoding="utf-8"))):
            if isinstance(no, ast.Call):
                chaves.update(_chaves_da_chamada(no))
    return chaves


def _existe(catalogo: dict, chave: str) -> bool:
    no: object = catalogo
    for parte in chave.split("."):
        if not isinstance(no, dict) or parte not in no:
            return False
        no = no[parte]
    return isinstance(no, str) and bool(no.strip())


def test_varredura_encontra_chaves_de_erro() -> None:
    chaves = _chaves_de_erro_usadas()
    assert {"ocorrencia.descricao_curta", "inquerito.ementa_curta", "laudo.tipo_invalido"} <= chaves


@pytest.mark.parametrize("idioma", ["pt", "en"])
def test_toda_chave_de_erro_tem_traducao(idioma: str) -> None:
    catalogo = json.loads((LOCALES / idioma / "default.json").read_text(encoding="utf-8"))

    faltando = sorted(c for c in _chaves_de_erro_usadas() if not _existe(catalogo, c))

    assert faltando == [], f"{len(faltando)} chave(s) sem tradução em {idioma}: {faltando}"
