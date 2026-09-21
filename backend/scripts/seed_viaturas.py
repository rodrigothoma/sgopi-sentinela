"""Seed de frota fictícia (RF02) — chamado por scripts/seed.py."""
from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from adapters.outbound.persistence.viatura_repositorio_sqlalchemy import ViaturaRepositorioSQLAlchemy  # noqa: E402
from domain.shared.geo import Coordenada  # noqa: E402
from domain.viatura.entity import Posicao, SituacaoViatura, Viatura  # noqa: E402
from infrastructure.database.connection import AsyncSessionLocal  # noqa: E402

# Frota fictícia georreferenciada na malha urbana de Alegrete-RS
VIATURAS = [
    ("VTR-01", "IAB1A23", -29.7842, -55.7932, SituacaoViatura.DISPONIVEL),       # Praça Getúlio Vargas / Centro
    ("VTR-02", "IBC2B34", -29.7880, -55.7910, SituacaoViatura.EM_DESLOCAMENTO),  # Rua dos Andradas
    ("VTR-03", "ICD3C45", -29.7785, -55.7915, SituacaoViatura.DISPONIVEL),       # Parque Rui Ramos
    ("VTR-04", "IDE4D56", -29.7910, -55.7890, SituacaoViatura.DISPONIVEL),       # Av. Assis Brasil
    ("VTR-05", "IEF5E67", -29.7750, -55.8010, SituacaoViatura.DISPONIVEL),       # Cidade Alta
]


async def semear_viaturas() -> None:
    agora = datetime.now(UTC)
    async with AsyncSessionLocal() as session:
        repo = ViaturaRepositorioSQLAlchemy(session)
        for prefixo, placa, lat, lon, situacao in VIATURAS:
            posicao = Posicao(coordenada=Coordenada(latitude=lat, longitude=lon), registrada_em=agora)
            existente = await repo.buscar_por_prefixo(prefixo)
            if existente:
                if existente.ultima_posicao is None:
                    existente.ultima_posicao = posicao
                    existente.situacao = situacao
                    existente.atualizada_em = agora
                    await repo.salvar(existente)
                    print(f"  ~ viatura '{prefixo}' atualizada com telemetria inicial ({lat:.4f}, {lon:.4f})")
                else:
                    print(f"  = viatura '{prefixo}' já existe")
                continue
            vtr = Viatura(
                prefixo=prefixo,
                placa=placa,
                situacao=situacao,
                ultima_posicao=posicao,
                atualizada_em=agora,
            )
            await repo.salvar(vtr)
            print(f"  + viatura '{prefixo}' ({placa}) em ({lat:.4f}, {lon:.4f}) - {situacao.value}")
        await session.commit()
