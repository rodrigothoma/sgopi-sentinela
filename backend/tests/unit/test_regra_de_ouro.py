"""
RNF05*: domain/ e application/ não importam frameworks nem camadas externas.
Complementa o import-linter (que roda no CI) com uma verificação na suíte normal.
"""
import ast
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
PROIBIDOS_DOMAIN = {"application", "adapters", "infrastructure", "fastapi", "starlette", "sqlalchemy", "pydantic", "jose", "argon2", "alembic", "httpx"}
PROIBIDOS_APPLICATION = PROIBIDOS_DOMAIN - {"application"}


def _imports(arquivo: Path) -> set[str]:
    arvore = ast.parse(arquivo.read_text(encoding="utf-8"))
    nomes: set[str] = set()
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            nomes.update(a.name.split(".")[0] for a in no.names)
        elif isinstance(no, ast.ImportFrom) and no.module:
            nomes.add(no.module.split(".")[0])
    return nomes


@pytest.mark.parametrize("arquivo", sorted((SRC / "domain").rglob("*.py")), ids=lambda p: str(p.relative_to(SRC)))
def test_domain_e_puro(arquivo: Path):
    assert not (_imports(arquivo) & PROIBIDOS_DOMAIN), f"{arquivo} importa camada/lib proibida"


@pytest.mark.parametrize("arquivo", sorted((SRC / "application").rglob("*.py")), ids=lambda p: str(p.relative_to(SRC)))
def test_application_so_importa_domain(arquivo: Path):
    assert not (_imports(arquivo) & PROIBIDOS_APPLICATION), f"{arquivo} importa camada/lib proibida"
