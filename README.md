# 🛡️ SGOPI Sentinela — Sistema de Gestão de Ocorrências Policiais Integradas

[![Arquitetura Hexagonal](https://img.shields.io/badge/Architecture-Hexagonal%20Ports%20%26%20Adapters-blue.svg)](#-arquitetura-do-software)
[![UML](https://img.shields.io/badge/Modelagem-UML-green.svg)](docs/DOCUMENTACAO_DE_ENGENHARIA.md)
[![Unipampa](https://img.shields.io/badge/Unipampa-Engenharia%20de%20Software-red.svg)](https://unipampa.edu.br/alegrete/)

O **SGOPI Sentinela** é uma solução de software para segurança pública desenvolvida com foco em **alta confiabilidade, tempo real, integridade de auditoria e desacoplamento arquitetural**. O sistema abrange desde o registro circunstanciado de ocorrências policiais e triagem técnica pelo Delegado até o monitoramento georreferenciado de viaturas em tempo real, inteligência de manchas criminais e gestão da cadeia de custódia.

O projeto e a arquitetura foram concebidos e modelados inicialmente na disciplina de **Análise e Projeto de Software (AL0332)**. Na disciplina atual de **Resolução de Problemas IV (AL0343)** do curso de **Engenharia de Software da Universidade Federal do Pampa (Unipampa - Campus Alegrete)**, a equipe consolidou a documentação técnica, a modelagem UML e o planejamento do MVP para guiar o ciclo de desenvolvimento e implementação do software.

---

## 📁 Estrutura do Repositório (Monorepo)

```
sgopi-sentinela/
├── backend/                       # API Python (FastAPI) — Arquitetura Hexagonal
│   ├── src/
│   │   ├── domain/                # Entidades, VOs e serviços de domínio puros (sem libs)
│   │   │   ├── ocorrencia/        # Ocorrencia (agregado), StatusOcorrencia + transições, eventos
│   │   │   ├── viatura/           # Viatura, SituacaoViatura, Posicao
│   │   │   ├── despacho/          # OrdemDeDespacho, serviço de proximidade (Haversine)
│   │   │   ├── usuario/           # Usuario, Papel
│   │   │   ├── auditoria/         # RegistroAuditoria
│   │   │   └── shared/            # Exceções (com chave i18n), Coordenada, CPF, eventos
│   │   ├── application/
│   │   │   ├── ports/inbound/     # Interface* + DTOs + Ator (um arquivo por caso de uso)
│   │   │   ├── ports/outbound/    # Repositorio*, UnidadeDeTrabalho, Relogio, GeradorProtocolo,
│   │   │   │                      # PortaAuditoria, PublicadorEventos, HasherSenha, ProvedorToken
│   │   │   └── use_cases/         # auth/, ocorrencia/, viatura/, despacho/, auditoria/
│   │   ├── adapters/
│   │   │   ├── inbound/http/      # deps (JWT/RBAC), erros, middleware, v1/*_router.py
│   │   │   ├── inbound/websocket/ # WS /v1/tempo-real + GerenciadorConexoes
│   │   │   ├── inbound/simulador/ # SimuladorTelemetria (driving adapter de GPS)
│   │   │   └── outbound/          # persistence/ (SQLAlchemy), seguranca/ (argon2, jose),
│   │   │                          # eventos/ (fan-out em memória), relogio/
│   │   ├── infrastructure/
│   │   │   ├── config/            # Settings (pydantic-settings, .env)
│   │   │   ├── database/          # engine, models, migrations/ (Alembic)
│   │   │   ├── i18n/              # mensagens pt/en
│   │   │   ├── logging.py         # logs JSON com request_id + máscara de CPF
│   │   │   └── di.py              # Composition Root (única ponte portas ↔ adapters)
│   │   └── main.py                # criar_app(): middleware, handlers, routers, /health
│   ├── scripts/seed.py            # Seed reproduzível (usuários + frota fictícia)
│   ├── tests/                     # fakes/, unit/, integration/ (SQLite em memória)
│   ├── alembic.ini · pyproject.toml · .env.example
├── frontend/                      # SPA React + TypeScript + Leaflet
│   └── src/ {components, pages, services, hooks, types}
├── docs/
│   ├── DOCUMENTACAO_DE_ENGENHARIA.md · PLANEJAMENTO_DESENVOLVIMENTO.md
│   └── diagramas/
├── docker-compose.yml             # PostgreSQL 16 local
└── README.md
```

> **Regra de ouro:** `domain/` e `application/` **nunca** importam FastAPI, SQLAlchemy ou qualquer lib externa. Apenas `adapters/` e `infrastructure/` podem. Verificado por `import-linter` e por um teste da suíte.

---

## 🚀 Como Rodar Localmente

### Pré-requisitos
- Python ≥ 3.13 + [uv](https://docs.astral.sh/uv/)
- Docker + Docker Compose (para o banco local)
- Node.js ≥ 20 (para o frontend)

### Backend

```bash
cd backend

# 1. Suba o banco local
docker compose -f ../docker-compose.yml up -d

# 2. Instale dependências
uv sync

# 3. Configure o ambiente
cp .env.example .env            # ajuste JWT_SECRET_KEY e CORS_ORIGINS se necessário

# 4. Crie o esquema e os dados de demonstração
uv run alembic upgrade head
uv run python -m scripts.seed   # usuários agente/delegado/operador (senha Senha@123) + 5 viaturas

# 5. Rode o servidor (Swagger em http://localhost:8000/docs)
uv run uvicorn --app-dir src main:app --reload
```

> Sem Docker? Aponte `DATABASE_URL=sqlite+aiosqlite:///./sgopi.db` no `.env` — o esquema e os testes são portáveis.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev                     # http://localhost:3000 (proxy /v1 e WebSocket para o backend)
```

### 📋 Quadro de Desenvolvimento (Kanban GitHub Projects)
Todas as etapas e fatias verticais do projeto estão mapeadas e organizadas no [**Quadro Oficial de Desenvolvimento no GitHub Projects**](https://github.com/users/rodrigothoma/projects/2).

### 🚀 Fluxo de Demonstração Ponta a Ponta (Arquitetura Dual)
1. **Cidadão (Portal Público):** Acessa `http://localhost:3000/` com animação mecânica retrô via `<SplitFlapText />` → Clica em *Registrar Ocorrência* (`/registrar-cidadao`) → Preenche o fato e clica no mapa Leaflet para marcar a coordenada → Recebe o protocolo oficial `SGOPI-AAAA-NNNNNN` e acompanha o status em tempo real em `/consulta` — a mesma página aceita a chave de segurança de um BO emitido (ou o QR Code em `/autenticar/<chave>`) para conferir a autenticidade do documento (RF08).
2. **Delegado (Revisão & Triagem):** Clica em *Acesso Policial* (`/login`) e usa o atalho de demonstração da **Delegada** (`delegado` / `Senha@123`) → Acessa a *Fila de revisão* (`/fila`) → Identifica o registro do cidadão → *Valida* a ocorrência (gerando o hash SHA-256 da narrativa) ou devolve/rejeita com justificativa.
3. **Operador da Central (Despacho Tático):** Autentica-se como **Operador** (`operador` / `Senha@123`) → Acessa o *Painel tático* (`/painel`) → Ativa o *Simulador GPS* → Seleciona a ocorrência validada → *Despacha* uma das 3 viaturas mais próximas sugeridas pelo algoritmo de Haversine → *Encerra atendimento* com desfecho circunstanciado.

### Qualidade

```bash
cd backend
uv run pytest -q                                   # 258 testes (unitários + integração + E2E de API)
uv run pytest --cov                                # cobertura ≥ 80 % em domain/ + application/ (atual ≈ 98 %)

PYTHONPATH=src uv run lint-imports --config pyproject.toml   # contratos da Arquitetura Hexagonal
cd ../frontend && npx tsc --noEmit && npm run build
```

### Testes E2E (Issues #21 e #22)

Pré-requisito: **backend** (`uv run uvicorn --app-dir src main:app --reload`) e **frontend** (`npm run dev`) rodando simultaneamente.

```bash
# Frontend (Cypress) — 18 testes (registro, validação, despacho)
cd frontend
npm run e2e            # headless
npm run e2e:open       # interface gráfica do Cypress (ver "Visualização" abaixo)

# Backend (pytest E2E de API) — 12 testes contra o servidor real em :8000
cd backend
uv run pytest tests/e2e -q
```

**Reset do banco E2E** (útil antes da primeira rodada ou se o estado estiver estranho):
```bash
cd frontend && npm run e2e:db
```

**Visualização dos testes (Cypress):**

- **Modo interativo (recomendado)** — abre o Cypress App com snapshots por passo:
  ```bash
  cd frontend && npm run e2e:open
  ```
  No app: escolha *E2E Testing* → navegador (Chrome/Edge) → clique na spec (`registro.cy.ts` ou `validacao-despacho.cy.ts`).  
  Você verá **em tempo real** o navegador preenchendo o formulário, clicando no mapa, trocando de tela.  
  À esquerda, o **log de cada comando** com ✅/❌; clique num passo para ver o **snapshot da tela naquele instante** (time-travel debugging).

- **Modo headed (navegador visível, sem UI do Cypress):**
  ```bash
  cd frontend && npx cypress run --headed --browser chrome
  ```

- **Evidências de falha:** se um teste falhar, o Cypress salva automaticamente **screenshots** em `frontend/cypress/screenshots/`.  
  Para gravar vídeo da execução, adicione `"video": true` no `cypress.config.ts` e rode `npm run e2e`.

> **Dica:** deixe `npm run e2e:open` rodando enquanto edita testes — ele re-roda ao salvar o arquivo.

---

## 📚 Documentação Técnica e Wiki

| Documento | Localização | Descrição |
| :--- | :--- | :--- |
| 📋 **Quadro Kanban Oficial** | [**GitHub Projects #2**](https://github.com/users/rodrigothoma/projects/2) | Backlog e esteira de desenvolvimento do projeto do início ao fim (49 itens rastreáveis). |
| 📄 **Especificação Completa de Engenharia** | [**docs/DOCUMENTACAO_DE_ENGENHARIA.md**](docs/DOCUMENTACAO_DE_ENGENHARIA.md) | Requisitos canônicos (RF01–RF10, RNF01–RNF05), matriz MoSCoW, proposta de MVP e casos de uso com diagramas de sequência. |
| 🗓️ **Planejamento de Desenvolvimento** | [**docs/PLANEJAMENTO_DESENVOLVIMENTO.md**](docs/PLANEJAMENTO_DESENVOLVIMENTO.md) | Cronograma de desenvolvimento e fatias verticais semanais da equipe (Sprints 2 a 5). |
| 🌐 **Wiki Oficial do Projeto** | [**GitHub Wiki**](https://github.com/rodrigothoma/sgopi-sentinela/wiki) | Base de conhecimento da equipe com guias, modelagem UML navegável e detalhamento arquitetural. |
| 📊 **Artefatos e Diagramas** | [**docs/diagramas/**](docs/diagramas/) | Todos os diagramas UML em alta definição. |

---

## 🎯 Proposta do MVP (Minimum Viable Product)

```
[ Cidadão (Portal Web Público) ] ──(Registro Online)──┐
                                                      ├──► [ Núcleo SGOPI ] ◄──(Revisão/Validação)── [ Delegado ]
[ Agente Policial (Delegacia) ]  ──(Reg. Circunst.)───┘            │
                                                                   ▼ (Status: Validada)
[ Viatura Policial ] ◄──────────(Despacho Tático)───────── [ Operador Central (Mapa GPS Real-Time) ]
```

### Matriz de Priorização (MoSCoW)
- **Must Have (MVP Essencial):** RF01 (Gestão de Ocorrência Policial), RF04 (Fluxo de Validação pelo Delegado) e RF02 (Monitoramento GPS e Despacho Tático).
- **Should Have (Alta Prioridade):** RF03 (Inventário de Apreensões), RF05 (Manchas Criminais e Alertas), RF07 (Laudos Periciais).
- **Could Have (Média Prioridade):** RF06 (Vinculação a Inquéritos), RF08 (Autenticação Pública de Documentos), RF09 (Medidas Protetivas).
- **Won't Have (Próximos Ciclos):** RF10 (Comunicação Interagências).

---

## 🏛️ Arquitetura do Software (Ports & Adapters)

O projeto adota a **Arquitetura Hexagonal** para garantir o isolamento estrito das regras de negócio de domínio:

* **Core Domain & Use Cases:** Regras de negócio puras (entidades e casos de uso) independentes de frameworks e bibliotecas externas (**RNF05**).
* **Inbound Ports & Adapters:** Endpoints REST e WebSockets reativos (**RNF01**).
* **Outbound Ports & Adapters:** Repositórios PostgreSQL, telemetria GPS, logs de auditoria imutáveis (**RNF03**) e RBAC (**RNF02**).

---

## 💻 Stack Tecnológica

| Camada | Tecnologia |
| :--- | :--- |
| Backend | Python 3.13 + FastAPI |
| ORM / DB | SQLAlchemy 2.0 (async) + Alembic |
| Banco de dados | PostgreSQL 16 |
| Dev local | Docker Compose |
| Produção/Demo | Supabase (PostgreSQL gerenciado) |
| Frontend | React + TypeScript + Vite |
| Mapa tático | Leaflet + OpenStreetMap |
| Tempo real | WebSockets |
| Testes | pytest + pytest-asyncio |
| Gerenciador deps | uv |

---

## ⚙️ Estratégia de Banco de Dados

O projeto usa **duas configurações de banco**, selecionáveis via `.env`:

- **Desenvolvimento local:** Docker Compose sobe um PostgreSQL 16; o esquema é versionado por **Alembic** (`alembic upgrade head`) e os dados de demonstração vêm de `scripts/seed.py` (idempotente, dados fictícios). Nenhum dado real é consumido.
- **Apresentação/Demo:** Supabase (PostgreSQL gerenciado). Basta comentar/descomentar a `DATABASE_URL` no `.env`.

---

## ⚙️ Estratégia de Qualidade

- **Testes unitários** (pytest): cobertura ≥ 80% sobre domínio e use cases — sem banco, sem servidor (fakes de todas as portas em `tests/fakes/`).
- **Testes de integração**: adapters e API (HTTP + WebSocket) contra SQLite em memória; esquema Postgres validado por `alembic check`.
- **Aderência hexagonal**: `import-linter` (3 contratos) + teste da regra de ouro na suíte.
- **Testes E2E** (Selenium): fluxos críticos do frontend — *previsto para a Sprint 5*.

---

## 📐 Modelagem e Artefatos de Projeto

- Diagrama de Casos de Uso
- Diagrama de Pacotes (camadas hexagonais)
- Diagramas de Componentes (executável e hexagonal)
- Diagrama de Classes de Domínio
- Diagramas de Sequência `sq01` a `sq11`
- Diagrama de Implantação

👉 Acesse a [**Documentação de Engenharia**](docs/DOCUMENTACAO_DE_ENGENHARIA.md) ou a [**Wiki**](https://github.com/rodrigothoma/sgopi-sentinela/wiki).

---

## 👥 Equipe de Desenvolvimento

* **Fade Hassan Husein Kanaan**
* **Gabriel Ortiz**
* **Gustavo Fernandes dos Anjos**
* **Mateus Estivalet Valau**
* **Matheus Cabral**
* **Rodrigo Thoma da Silva**

### 🎓 Corpo Docente / Orientação
* **Prof. Dr. Fabio Paulo Basso**
* **Prof. Dr. Gilleanes Thorwald Araujo Guedes**
