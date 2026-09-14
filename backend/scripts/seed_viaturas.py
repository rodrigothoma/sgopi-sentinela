"""Seed de frota fictícia (RF15) — chamado por scripts/seed.py."""
from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from adapters.outbound.persistence.viatura_repositorio_sqlalchemy import ViaturaRepositorioSQLAlchemy  # noqa: E402
from domain.viatura.entity import Viatura  # noqa: E402
from infrastructure.database.connection import AsyncSessionLocal  # noqa: E402

VIATURAS = [("VTR-01", "IAB1A23"), ("VTR-02", "IBC2B34"), ("VTR-03", "ICD3C45"), ("VTR-04", "IDE4D56"), ("VTR-05", "IEF5E67")]


async def semear_viaturas() -> None:
    async with AsyncSessionLocal() as session:
        repo = ViaturaRepositorioSQLAlchemy(session)
        for prefixo, placa in VIATURAS:
            if await repo.buscar_por_prefixo(prefixo):
                print(f"  = viatura '{prefixo}' já existe")
                continue
            await repo.salvar(Viatura(prefixo=prefixo, placa=placa, atualizada_em=datetime.now(UTC)))
            print(f"  + viatura '{prefixo}' ({placa})")
        await session.commit()
