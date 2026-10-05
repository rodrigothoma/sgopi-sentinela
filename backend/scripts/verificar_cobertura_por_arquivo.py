"""
Piso de cobertura por arquivo (N10): a média agregada (≥ 80%) escondia módulos com 22% e 43%.

Uso (depois de ``uv run pytest --cov --cov-report=json``):
    uv run python -m scripts.verificar_cobertura_por_arquivo [coverage.json]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# prefixo → cobertura mínima (%) de cada arquivo sob ele
PISOS = {"src/domain/": 85.0, "src/application/": 75.0}


def abaixo_do_piso(relatorio: dict) -> list[tuple[str, float, float]]:
    falhas = []
    for arquivo, dados in relatorio["files"].items():
        piso = next((p for prefixo, p in PISOS.items() if arquivo.startswith(prefixo)), None)
        percentual = dados["summary"]["percent_covered"]
        if piso is not None and percentual < piso:
            falhas.append((arquivo, percentual, piso))
    return sorted(falhas)


def main(caminho: str = "coverage.json") -> int:
    falhas = abaixo_do_piso(json.loads(Path(caminho).read_text(encoding="utf-8")))
    for arquivo, percentual, piso in falhas:
        print(f"{arquivo}: {percentual:.1f}% < piso de {piso:.0f}%")
    if not falhas:
        print("Cobertura por arquivo: todos os módulos acima do piso.")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
