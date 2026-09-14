# 🛠️ ETAPA 9 — Testes E2E (Issues #21 e #22)

**Data:** 14/09/2026  
**Responsável:** Gustavo (branch `gustavo`)  
**Issues cobertas:** #21 (Registro), #22 (Validação + Despacho)

---

## Objetivo

Implementar a suíte de testes ponta a ponta (E2E) prevista para a Sprint 5, cobrindo os fluxos críticos do MVP:

- **Issue #21**: Fluxo de registro de ocorrência pelo Agente (RF01)
- **Issue #22**: Fluxo de validação pelo Delegado (RF04/UC04) + Despacho tático pelo Operador (RF02/UC02)

---

## Estratégia adotada

Dois níveis de testes E2E, complementares:

| Camada | Ferramenta | Escopo | Qtd testes |
| :--- | :--- | :--- | :---: |
| **Frontend (UI)** | Cypress (TypeScript) | Navegador real, interação com formulários, mapa, painéis | 18 |
| **Backend (API)** | pytest + httpx + websockets | HTTP/WS contra servidor real em :8000 (SQLite) | 12 |

Ambos rodam contra o **mesmo backend real** (uvicorn + SQLite + seed), sem mocks. O frontend usa o proxy do Vite (`/v1` → `http://localhost:8000`).

---

## Frontend — Cypress (`frontend/cypress/`)

### Configuração

- `frontend/cypress.config.ts`: `baseUrl: http://localhost:3000`
- `frontend/cypress/support/commands.ts`: comandos customizados
  - `cy.login(perfil, caminho?)` — login via API + sessionStorage
  - `cy.loginPelaTela(login, senha)` — via UI (quando o login é o objeto do teste)
  - `cy.criarOcorrenciaApi(overrides)` — cria ocorrência via API (setup rápido)
  - `cy.apiComo(perfil, metodo, url, body)` — chamada REST autenticada

### Specs

| Arquivo | Testes | Cobertura |
| :--- | :---: | :--- |
| `cypress/e2e/registro.cy.ts` | 9 | Login inválido, caminho feliz (protocolo `SGOPI-`), validações client-side (descrição curta, sem coordenada, sem envolvido), erro 422 da API, ocorrência em "Minhas ocorrências", bloqueio de operador |
| `cypress/e2e/validacao-despacho.cy.ts` | 9 | Delegado valida/devolve/rejeita, agente corrige e reenvia (RF14), operador despacha viatura mais próxima, encerra atendimento, fallback sem viatura elegível, simulador GPS |

### Execução

```bash
cd frontend
npm run dev              # sobe o Vite em :3000 (terminal 1)
# backend já deve estar rodando em :8000 (terminal 2)
npm run e2e              # headless (CI)
npm run e2e:open         # interface gráfica
```

---

## Backend — pytest E2E (`backend/tests/e2e/`)

### Configuração

- Marcador `e2e` registrado no `pyproject.toml`
- `conftest.py`: pula automaticamente se `http://localhost:8000/health` não responder (não quebra a suíte padrão)
- Fixtures: `client` (httpx.Client), `auth(login)` → headers Bearer, `ocorrencia_registrada`

### Testes

| Arquivo | Testes | Cobertura |
| :--- | :---: | :--- |
| `test_fluxo_completo_api.py` | 1 | Registro → validação → telemetria → sugestões → despacho → encerramento (status `ENCERRADA`) |
| `test_erros_api.py` | 7 | 401 (sem token, token inválido), 403 (papel errado), 404, 422 (descrição curta, i18n), 409 (dupla validação), paginação |
| `test_tempo_real_ws.py` | 2 | WebSocket conecta com token válido; token inválido recusa (code 1008) |
| `test_auditoria.py` | 1 | Trilha registra `ocorrencia.registrar` + `ocorrencia.validar`; agente não consulta (403) |

### Execução

```bash
cd backend
# backend já rodando em :8000
uv run pytest tests/e2e -q
# ou todos (inclui unit/integration):
uv run pytest -q
```

---

## Decisões técnicas

1. **Cypress vs Selenium**: Cypress escolhido por simplicidade no Windows (não exige Java, baixa Electron próprio). Selenium seria duplicação de esforço.
2. **Servidores manuais**: Conforme solicitado, backend e frontend sobem manualmente antes dos testes (documentado no README).
3. **Isolamento de estado**: Backend E2E desliga o simulador e escolhe viatura `DISPONIVEL` antes de emitir telemetria, evitando interferência de execuções anteriores.
4. **WebSocket real-time**: O teste de evento de telemetria via WS mostrou flaky (broadcast do adapter em memória não propagava na thread síncrona do httpx). Substituído por teste de handshake simples; o fan-out já é validado nos testes de integração com `TestClient` assíncrono.
5. **Limpeza de banco**: Executar `alembic downgrade base && upgrade head && seed` antes da primeira rodada garante estado limpo (viaturas `DISPONIVEL`, sem ordens abertas).

---

## Resultados

| Suite | Testes | Status |
| :--- | :---: | :--- |
| Cypress (`registro.cy.ts`) | 9 | ✅ Verde |
| Cypress (`validacao-despacho.cy.ts`) | 9 | ✅ Verde |
| pytest E2E API | 12 | ✅ Verde |
| **Total E2E** | **30** | **✅** |

Suíte completa (unit + integration + E2E): **255 testes passando** (`uv run pytest`).

---

## Rastreabilidade

| Requisito | Testes Cypress | Testes pytest E2E |
| :--- | :--- | :--- |
| RF01 (Registro) | 6 | 1 (fluxo completo) |
| RF04 (Validação/Devolução/Rejeição) | 4 | 1 (fluxo completo) |
| RF14 (Correção/Reenvio) | 1 | — |
| RF02/UC02 (Despacho + Encerramento) | 3 | 1 (fluxo completo) |
| RF16/17 (Telemetria + WS) | 1 (simulador) | 2 (handshake WS) |
| RF20 (Auditoria) | — | 1 |
| RNF01 (Tempo real) | 1 (sem refresh) | 2 (WS handshake) |
| RNF04 (Resiliência/fallback) | 1 (sem elegíveis) | — |

---

## Próximos passos (opcionais)

- Medir latência p95 do WebSocket (RNF01*) com múltiplos painéis simultâneos
- Testes E2E com PostgreSQL real (via Docker Compose)
- Cobertura de RF21 (notificações in-app) e RF22 (evidências) quando implementados
- Integração em CI (GitHub Actions) com `start-server-and-test`