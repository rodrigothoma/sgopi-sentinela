"""
Seed de um documento emitido com chave fixa para demonstração do portal público (RF08) —
chamado por scripts/seed.py. Dados fictícios (RNF10).

A chave ``CHAVE_DEMO`` é a mesma exibida como dica na página /autenticar do frontend.
"""
from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from adapters.outbound.persistence.gerador_protocolo_sqlalchemy import GeradorProtocoloSQLAlchemy  # noqa: E402
from adapters.outbound.persistence.ocorrencia_repositorio_sqlalchemy import OcorrenciaRepositorioSQLAlchemy  # noqa: E402
from adapters.outbound.persistence.usuario_repositorio_sqlalchemy import UsuarioRepositorioSQLAlchemy  # noqa: E402
from domain.ocorrencia.autenticidade import normalizar_chave  # noqa: E402
from domain.ocorrencia.entity import Envolvido, Ocorrencia, TipificacaoPenal, TipoEnvolvido  # noqa: E402
from domain.shared.geo import Coordenada  # noqa: E402
from infrastructure.database.connection import AsyncSessionLocal  # noqa: E402

CHAVE_DEMO = normalizar_chave("SGPX-SENT-DEMX-CHAV-EXEM-PLAR")


async def semear_documento_demo() -> None:
    async with AsyncSessionLocal() as session:
        ocorrencias = OcorrenciaRepositorioSQLAlchemy(session)
        if await ocorrencias.buscar_por_chave_autenticidade(CHAVE_DEMO):
            print("  = documento demo já existe")
            return
        usuarios = UsuarioRepositorioSQLAlchemy(session)
        agente = await usuarios.buscar_por_login("agente")
        delegado = await usuarios.buscar_por_login("delegado")
        if agente is None or delegado is None:
            print("  ! documento demo ignorado: usuários 'agente' e 'delegado' são necessários")
            return

        agora = datetime.now(UTC)
        ocorrencia = Ocorrencia.registrar(
            agente_policial_id=agente.id,
            natureza="Furto",
            descricao="Furto de bicicleta estacionada em frente ao campus, sem violência ou grave ameaça. Registro fictício para demonstração.",
            localizacao="Av. Tiaraju, 810 — Alegrete/RS",
            coordenada=Coordenada(-29.7887, -55.7929),
            data_hora_fato=agora - timedelta(days=1, hours=2),
            numero_protocolo=await GeradorProtocoloSQLAlchemy(session).proximo(agora.year),
            agora=agora - timedelta(days=1),
            envolvidos=[Envolvido(nome="Vítima Fictícia", tipo=TipoEnvolvido.VITIMA)],
            tipificacoes=[TipificacaoPenal(artigo="Art. 155 CP", descricao="Furto simples")],
        )
        ocorrencia.validar(delegado.id, agora - timedelta(hours=20))
        ocorrencia.chave_autenticidade = CHAVE_DEMO  # chave previsível só para o ambiente de demonstração
        await ocorrencias.salvar(ocorrencia)
        await session.commit()
        print(f"  + documento demo {ocorrencia.numero_protocolo} (chave {CHAVE_DEMO})")
