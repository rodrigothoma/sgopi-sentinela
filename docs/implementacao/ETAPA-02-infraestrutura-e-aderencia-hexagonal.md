# ETAPA 02 — Infraestrutura e aderência hexagonal (persistência, transação, migrations, app base)

**Data:** 13/09/2026 · **Branch:** `matheus-Fastapi` · **Prioridade:** 🟠 alta (pré-requisito de todas as fatias)
**Origem:** `ETAPA-04` §5 (RNF03\*, RNF05\*, RNF07, RNF09, RNF11) e §6 (HEX-02, HEX-09, HEX-11, HEX-12); `ETAPA-05` NEXT-02 (CORS/seed), NEXT-03, NEXT-04, NEXT-16; DIV-21, DIV-22, DIV-23, DIV-24, DIV-25.

## 1. Objetivo

Dar ao domínio da Etapa 1 uma infraestrutura que respeite os RNFs: esquema versionado (Alembic), sem cascatas de exclusão, transação controlada pelo caso de uso, composição de dependências fora dos routers, erros padronizados e observabilidade mínima.

## 2. O que foi implementado

| Item | Arquivo | Requisito / lacuna |
| :--- | :--- | :--- |
| Settings ampliados: `cors_origins` (lista), JWT 8 h, parâmetros de telemetria/simulador/despacho, logs | `infrastructure/config/settings.py` + `.env.example` | RNF02\*, RNF07 |
| `get_session` como única dependência de banco; `criar_engine()` | `infrastructure/database/connection.py` | HEX-02 |
| Models reescritos com tipo `Uuid` portátil, `latitude/longitude`, `data_hora_fato`, `versao`, `atualizada_em`, `justificativa_revisao`, `desfecho`, `hash_narrativa`; **sem `cascade`/`ondelete`**; filhos com flag `ativo`; novas tabelas `usuarios`, `historico_status_ocorrencia`, `registros_auditoria`, `sequencias_protocolo` | `infrastructure/database/models.py` | HEX-12, DIV-24, RNF03\*, RNF-P10 |
| **Alembic** configurado (`alembic.ini`, `env.py` async, `script.py.mako`) e migration `0001_esquema_inicial` escrita à mão, com **trigger append-only** em `registros_auditoria` e `historico_status_ocorrencia` (Postgres) | `backend/alembic.ini`, `src/infrastructure/database/migrations/` | HEX-11, DIV-21, RNF07, RF20 aceite 2 |
| `create_all` **removido** do `lifespan` (fica só nos testes) | `main.py` | HEX-11 |
| `UnidadeDeTrabalhoSQLAlchemy` (detém `commit`/`rollback`) | `adapters/outbound/persistence/unidade_de_trabalho_sqlalchemy.py` | HEX-09, RNF11 |
| `OcorrenciaRepositorioSQLAlchemy` reescrito: não confirma transação; reconcilia filhos por *soft delete*; histórico append-only; **optimistic locking explícito** (`SELECT … FOR UPDATE` + comparação com a versão carregada → `ConflitoError` 409); filtro/paginação/ordenação; `contar` | `adapters/outbound/persistence/ocorrencia_repositorio_sqlalchemy.py` | RNF03\*, RNF11, RF13 |
| `AuditoriaSQLAlchemy` (append-only), `GeradorProtocoloSQLAlchemy` (upsert atômico `ON CONFLICT … RETURNING`, formato `SGOPI-AAAA-NNNNNN`), `RelogioSistema`, `PublicadorEventosEmMemoria` (fan-out assíncrono com isolamento de falhas) | `adapters/outbound/{persistence,relogio,eventos}/` | RF20, HEX-08, HEX-07, DEC-06 |
| `HasherArgon2` + porta `HasherSenha` (antecipado porque a fixture de usuários precisa de hash real) | `adapters/outbound/seguranca/hasher_argon2.py`, `application/ports/outbound/hasher_senha.py` | RF11 |
| **Composition root** `infrastructure/di.py`: `get_*` tipados pelas portas; routers nunca importam adapters | `infrastructure/di.py` | HEX-02, DIV-29 |
| Handlers globais: `DomainError` → 404/401/403/409/422 por tipo, `RequestValidationError` e `HTTPException` com corpo `{detail, code, request_id, extra}` e mensagem i18n por `Accept-Language` | `adapters/inbound/http/erros.py` | HEX-03, DIV-28, RNF08, RNF09 |
| Middleware `X-Request-ID` + log de requisição (`operacao`, `status`, `duracao_ms`); logging JSON com `request_id`/`usuario_id` via `ContextVar` | `adapters/inbound/http/middleware.py`, `infrastructure/logging.py` | RNF09 |
| `criar_app()` (fábrica), CORS por lista de origens, `/health` que executa `SELECT 1` e devolve `503 {db: down}` em falha | `main.py` | DIV-22, DIV-25, RNF04\*, RNF09 |
| i18n: 40+ chaves novas em `pt` e `en` cobrindo todas as exceções do domínio | `infrastructure/i18n/locales/*/default.json` | RNF08 |
| `docker-compose.yml`: removido o *mount* de `seed.sql` (rodava antes de existirem tabelas); `healthcheck` do Postgres; `backend/db/` removido — seed vira script Python na Etapa 3 | raiz | DIV-23, RNF07 |

## 3. Decisões tomadas durante a implementação

- **Docker não está acessível neste ambiente** (socket sem permissão). A suíte de integração roda em **SQLite em memória** (`aiosqlite` + `StaticPool`) com o mesmo `Base.metadata`; o esquema Postgres é validado por `alembic upgrade head` + `alembic check` (sem diferenças) + `downgrade base` num SQLite de arquivo. Os models usam apenas tipos portáveis (`Uuid`, `JSON`, `DateTime(timezone=True)`); datas naive vindas do SQLite são normalizadas para UTC no adapter (`_datas.aware`).
- **Optimistic locking:** o mecanismo nativo `version_id_col` do SQLAlchemy não detectou a colisão no cenário de duas sessões (o re-`SELECT` reidratou a versão), então o repositório passou a rastrear a versão carregada por instância e a comparar após `SELECT … FOR UPDATE`. É determinístico nos dois dialetos e cobre o critério "evita decisão dupla do Delegado" (RNF11).
- **Exclusão física proibida** (RNF03\*): `corrigir()` que remove envolvidos/tipificações resulta em `ativo = false`; a leitura devolve só os ativos. Não existe `DELETE` na API.
- O trigger append-only é criado **apenas em PostgreSQL** (`op.get_bind().dialect.name`), e o `downgrade` o remove.
- O router antigo `ocorrencias_router.py` foi **removido** (dependia de `get_db` e do DTO antigo); é reescrito na Etapa 3 já com autenticação.

## 4. Testes

```
uv run pytest -q   →   75 passed
```

| Arquivo | Cobre |
| :--- | :--- |
| `tests/integration/conftest.py` | engine SQLite em memória, `create_all`, seed de 4 usuários + 1 inativo com argon2, `app` com `get_session` sobrescrito, `client` httpx |
| `tests/integration/test_persistencia_ocorrencia.py` (7) | round-trip completo (coordenada, datas com fuso, filhos, histórico); transição persiste histórico append-only; correção desativa em vez de apagar; **conflito de versão entre duas sessões → `ConflitoError`**; listagem por status/ordem/paginação/agente; protocolo sequencial por ano; auditoria registra/lista |
| `tests/integration/test_app_base.py` (7) | `/health` 200/503; `X-Request-ID` propagado; mapa exceção→status com i18n `pt`/`en`; corpo padronizado de erro de validação; 404 padronizado; CORS aceita origem da lista e nega desconhecida |

Verificação adicional executada:
```
DATABASE_URL=sqlite+aiosqlite:///…/mig.db uv run alembic upgrade head   # OK
DATABASE_URL=… uv run alembic check                                     # "No new upgrade operations detected."
DATABASE_URL=… uv run alembic downgrade base                            # OK
```

## 5. Fora desta etapa

- Login, `Ator` a partir do JWT, RBAC nas rotas, seed de usuários → **Etapa 3**.
- Routers de ocorrências (registro, consulta, revisão) → **Etapas 3 e 4**.
- Execução contra Postgres real (requer Docker) — comandos documentados no README (Etapa 8).
- `import-linter` e cobertura mínima → **Etapa 8**.

## 6. Rastreabilidade

DIV-21 ✅ · DIV-22 ✅ · DIV-23 ✅ · DIV-24 ✅ · DIV-25 ✅ · DIV-28 ✅ (HTTP) · DIV-29 ✅ · HEX-02 ✅ · HEX-03 ✅ · HEX-09 ✅ · HEX-10 ✅ (adapters) · HEX-11 ✅ · HEX-12 ✅ · RNF03\* ✅ (esquema) · RNF07 ✅ (parcial — seed na Etapa 3) · RNF08 ✅ · RNF09 ✅ · RNF11 ✅
