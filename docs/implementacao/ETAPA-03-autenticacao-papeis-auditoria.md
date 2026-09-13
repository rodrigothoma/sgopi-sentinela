# ETAPA 03 — Autenticação, papéis e auditoria (RF11, RF12, RF20, RNF02\*)

**Data:** 13/09/2026 · **Branch:** `matheus-Fastapi` · **Prioridade:** 🔴 bloqueante (critério de aceite 2 do MVP: "somente Delegado valida")
**Origem:** `ETAPA-04` §4 (RF11, RF12, RF20), §5 (RNF02\*); `ETAPA-05` NEXT-06, NEXT-07; DIV-20, RNF-P04, RNF-P05, RNF-P06, HEX-14 (parte backend).

## 1. Objetivo

Eliminar o `agente_policial_id` vindo do body (falha de segurança apontada na análise), colocar toda rota atrás de token JWT de turno (8 h) e fazer o RBAC por papel com auditoria de negações.

## 2. O que foi implementado

| Item | Arquivo | Requisito |
| :--- | :--- | :--- |
| Portas `RepositorioUsuario`, `ProvedorToken` (+ `DadosToken`), `HasherSenha` (Etapa 2) | `application/ports/outbound/` | RF11, RF12 |
| Porta de entrada `InterfaceAutenticarUsuario` (+ DTOs) | `application/ports/inbound/interface_autenticar_usuario.py` | RF11 |
| Caso de uso `AutenticarUsuario`: login *case-insensitive*, resposta 401 **idêntica** para login inexistente / senha errada / usuário inativo (não vaza existência de login), auditoria de sucesso e de falha com motivo | `application/use_cases/auth/autenticar_usuario.py` | RF11, RF12 aceite 2, RF20 |
| `UsuarioRepositorioSQLAlchemy` | `adapters/outbound/persistence/usuario_repositorio_sqlalchemy.py` | RF12 |
| `ProvedorTokenJose` (HS256, claims `sub`, `login`, `papel`, `iat`, `exp`; expiração verificada com a porta `Relogio` → testável) | `adapters/outbound/seguranca/provedor_token_jose.py` | RF11, RNF02\* |
| `HasherArgon2` (argon2id) | `adapters/outbound/seguranca/hasher_argon2.py` | RNF02\* |
| Dependências `ator_atual()` (Bearer → `Ator`, popula `usuario_id` no log) e `exigir_papel(*papeis)` (negação → auditoria `auth.acesso_negado` com rota + 403) | `adapters/inbound/http/deps.py` | RF12, RF20, RNF09 |
| `POST /v1/auth/login`, `GET /v1/auth/me` | `adapters/inbound/http/v1/auth_router.py` | RF11 |
| `POST /v1/ocorrencias` reescrito: exige `AGENTE`, ator do token, `latitude/longitude/data_hora_fato` no contrato | `adapters/inbound/http/v1/ocorrencias_router.py` | RF01\* critério 5 |
| Wiring no composition root (`get_hasher`, `get_provedor_token`, `get_repositorio_usuario`, `get_autenticar_usuario`) | `infrastructure/di.py` | HEX-02 |
| **Seed reproduzível** `scripts/seed.py` (idempotente; 3 usuários, senha `Senha@123`, dados fictícios) | `backend/scripts/seed.py` | RF12 aceite 1, RNF07, RNF10 |

## 3. Decisões tomadas durante a implementação

- **Token stateless**: a validação do token não consulta o banco (o *claim* `papel` basta). Consequência aceita no MVP: desativar um usuário não revoga tokens já emitidos até expirarem (8 h). Registrado como dívida para um ciclo com *blacklist*/versão de sessão.
- **Defesa em profundidade**: o papel é verificado duas vezes — na dependência da rota (`exigir_papel`, que audita) e dentro do caso de uso (`Ator.exigir_papel`). Um caso de uso chamado por outro adapter (p.ex. simulador ou CLI) continua protegido.
- O IP do cliente (`X-Forwarded-For` ou `request.client.host`) viaja em `Ator.ip` e é gravado na auditoria; o caso de uso não conhece HTTP.
- `agente_policial_id` enviado no body é **ignorado silenciosamente** (schema Pydantic não o declara) — testado.
- O seed usa as mesmas portas/adapters da aplicação (não SQL cru), então respeita hashing e regras da entidade.

## 4. Testes

```
uv run pytest -q   →   105 passed
```

| Arquivo | Cobre |
| :--- | :--- |
| `tests/unit/use_cases/test_autenticar_usuario.py` (7) | token 8 h, login *case-insensitive*, 4 cenários de falha auditados com motivo, expiração via `Relogio` |
| `tests/unit/adapters/test_provedor_token_jose.py` (5) | emissão/decodificação, expirado, segredo diferente, token lixo, argon2 |
| `tests/integration/test_auth_http.py` (9) | login 200/401 (i18n), inativo, sem token 401 + `WWW-Authenticate`, `/me`, token adulterado, token expirado, **Delegado tentando registrar → 403 auditado com rota**, logins auditados |
| `tests/integration/test_ocorrencias_http.py` (9) | 201 + protocolo `SGOPI-AAAA-000001` + `AGUARDANDO_REVISAO` + auditoria; **`agente_policial_id` do body ignorado**; 422 i18n `pt`/`en` sem envolvido; latitude 91; data futura; CPF inválido; descrição curta com `extra.minimo`; body malformado; protocolos sequenciais |

Verificação adicional: `uv run python -m scripts.seed` executado duas vezes contra um SQLite migrado — cria 3 usuários e, na segunda execução, reporta "já existe" (idempotente).

## 5. Fora desta etapa

- Tela de login e armazenamento do token no frontend → **Etapa 7**.
- Consulta/revisão/correção de ocorrências (usa `exigir_papel(Papel.DELEGADO)`) → **Etapa 4**.
- Máscara de CPF por papel nas respostas (RNF10) → **Etapa 8**.

## 6. Rastreabilidade

DIV-20 ✅ · RNF-P04 ✅ · RNF-P05 ✅ (enum `Papel`) · RNF-P06 ✅ (argon2, JWT 8 h, CORS por lista) · RF-P16 ✅ · RF11 ✅ · RF12 ✅ · RF20 ✅ (login, negação, registro) · RNF02\* ✅ (exceto HTTPS, que é responsabilidade do *deploy*) · DIV-23 ✅ (seed por script)
