"""
Seed reproduzível de desenvolvimento/demo (RNF07, RF12, DIV-23).

    uv run alembic upgrade head
    uv run python -m scripts.seed

Idempotente: usuários e viaturas já existentes (por login/prefixo) são mantidos.
Dados fictícios (RNF10). Senha padrão de todos os usuários: ``Senha@123``.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from adapters.outbound.persistence.usuario_repositorio_sqlalchemy import UsuarioRepositorioSQLAlchemy  # noqa: E402
from adapters.outbound.seguranca.hasher_argon2 import HasherArgon2  # noqa: E402
from domain.usuario.entity import Papel, Usuario  # noqa: E402
from infrastructure.database.connection import AsyncSessionLocal  # noqa: E402

SENHA_PADRAO = "Senha@123"

USUARIOS = [
    ("Agente Silva", "agente", Papel.AGENTE),
    ("Delegada Souza", "delegado", Papel.DELEGADO),
    ("Operador Lima", "operador", Papel.OPERADOR_CENTRAL),
]


async def semear_usuarios() -> None:
    hasher = HasherArgon2()
    async with AsyncSessionLocal() as session:
        repo = UsuarioRepositorioSQLAlchemy(session)
        for nome, login, papel in USUARIOS:
            if await repo.buscar_por_login(login):
                print(f"  = usuário '{login}' já existe")
                continue
            await repo.salvar(Usuario(nome=nome, login=login, senha_hash=hasher.gerar_hash(SENHA_PADRAO), papel=papel))
            print(f"  + usuário '{login}' ({papel.value})")
        await session.commit()


async def main() -> None:
    print("Seed SGOPI Sentinela")
    await semear_usuarios()
    try:
        from scripts.seed_viaturas import semear_viaturas
        await semear_viaturas()
    except ImportError as e:
        print(f"  ! Não foi possível carregar seed_viaturas: {e}")

    try:
        from scripts.seed_ocorrencias import semear_ocorrencias
        await semear_ocorrencias()
    except ImportError as e:
        print(f"  ! Não foi possível carregar seed_ocorrencias: {e}")

    try:
        from scripts.seed_documento_demo import semear_documento_demo  # Etapa 9 (RF08)
        await semear_documento_demo()
    except ImportError as e:
        print(f"  ! Não foi possível carregar seed_documento_demo: {e}")


if __name__ == "__main__":
    asyncio.run(main())

