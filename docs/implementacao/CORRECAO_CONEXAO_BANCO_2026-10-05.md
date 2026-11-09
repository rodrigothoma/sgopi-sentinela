# Correção — Falha de conexão com o banco no setup local (2026-10-05)

## Sintoma

Ao seguir o roteiro de setup do backend (`docker compose up` → `alembic upgrade head` → `scripts.seed`):

```
failed to connect to the docker API at unix:///home/matheus/.docker/desktop/docker.sock ... no such file or directory
...
asyncpg.exceptions.InvalidPasswordError: password authentication failed for user "postgres"
```

Tanto o Alembic quanto o seed falhavam na primeira conexão com o banco.

## Diagnóstico

O código da aplicação **não** estava quebrado. Eram duas falhas de ambiente encadeadas:

| # | Causa | Evidência |
|---|-------|-----------|
| 1 | O Docker CLI usa o contexto `desktop-linux` (Docker Desktop), mas o Docker Desktop estava parado. O `docker compose up` falhou e o container `sgopi_db` nunca subiu. | `docker context ls` → `desktop-linux *`; `docker-desktop.service` (user) desativado. O daemon nativo (`/var/run/docker.sock`) também não servia de alternativa: o usuário não está no grupo `docker`. |
| 2 | Um **PostgreSQL 18 nativo** do sistema (`postgresql.service`) já escuta em `127.0.0.1:5432`. Sem o container, o backend conectou nesse servidor, que tem outra senha para `postgres`. Daí o `InvalidPasswordError`, que escondia a causa real. | `ss -ltnp` → `127.0.0.1:5432`; processo `/usr/lib/postgresql/18/bin/postgres`. |

Mesmo com o Docker funcionando, publicar o container em `5432` continuaria colidindo com o PostgreSQL nativo: `localhost:5432` cairia no servidor errado (ou o bind da porta falharia).

## Correção aplicada

### Ambiente (máquina local)
- Docker Desktop iniciado: `systemctl --user start docker-desktop`.
  Para subir junto com a sessão: `systemctl --user enable docker-desktop`.

### Repositório
| Arquivo | Mudança |
|---------|---------|
| `docker-compose.yml` | A porta do host passa a ser configurável, com padrão `5433`: `"${SGOPI_DB_PORTA:-5433}:5432"`. |
| `backend/.env.example` | `DATABASE_URL` aponta para `localhost:5433`, com um comentário explicando o motivo. |
| `backend/alembic.ini` | `sqlalchemy.url` de fallback → `localhost:5433`. |
| `backend/src/infrastructure/config/settings.py` | Default de `database_url` → `localhost:5433`. |
| `backend/.env` (local, ignorado pelo git) | `DATABASE_URL` → `localhost:5433`. |

O CI (`.github/workflows/ci.yml`) usa o próprio service container e o próprio `DATABASE_URL`, então não é afetado.

> **Para quem já tem um `backend/.env`:** troque `localhost:5432` por `localhost:5433` no `DATABASE_URL`. Se preferir manter a 5432 (sem PostgreSQL nativo na máquina), exporte `SGOPI_DB_PORTA=5432` antes do `docker compose up` e ajuste o `.env` para combinar.

## Verificação

| Etapa | Resultado |
|-------|-----------|
| `docker compose -f ../docker-compose.yml up -d --wait` | `sgopi_db` **Healthy** |
| `uv run alembic upgrade head` | Migrações `0001` → `0016` aplicadas |
| `uv run python -m scripts.seed` | Usuários, viaturas e 12 ocorrências criados |
| `uvicorn ... main:app` | `/docs` HTTP 200; login `agente` / `Senha@123` retorna `access_token` |
| `PYTHONPATH=src uv run lint-imports` | 4 contratos mantidos, 0 quebrados |
| `uv run pytest --cov` | 744 testes passaram; cobertura 95,64% |

O frontend não foi alterado, então `tsc`/`build` não foram executados.

## Alternativas descartadas
- **Parar o PostgreSQL nativo** (`sudo systemctl stop postgresql`): exige sudo e pode afetar outros projetos da máquina.
- **Usar o daemon nativo** (`docker context use default`): exige adicionar o usuário ao grupo `docker` (equivale a acesso root) e não resolve o conflito de porta.
