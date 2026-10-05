# 🛡️ SGOPI Sentinela — Sistema de Gestão de Ocorrências Policiais Integradas

[![Arquitetura Hexagonal](https://img.shields.io/badge/Architecture-Hexagonal%20Ports%20%26%20Adapters-blue.svg)](#-arquitetura-do-software)
[![UML](https://img.shields.io/badge/Modelagem-UML-green.svg)](docs/DOCUMENTACAO_DE_ENGENHARIA.md)
[![Unipampa](https://img.shields.io/badge/Unipampa-Engenharia%20de%20Software-red.svg)](https://unipampa.edu.br/alegrete/)

O **SGOPI Sentinela** é uma solução de software para segurança pública desenvolvida com foco em **alta confiabilidade, tempo real, integridade de auditoria e desacoplamento arquitetural**. O MVP abrange o registro circunstanciado de ocorrências policiais (RF01), a triagem técnica pelo Delegado (RF04) e o monitoramento georreferenciado de viaturas em tempo real com despacho tático (RF02). Além do MVP, a equipe implementou módulos **extras** — manchas criminais, apreensões com cadeia de custódia, inquéritos, laudos, medidas protetivas e autenticação pública de documentos (ver [Extras implementados](#-extras-implementados-além-do-mvp)).

O projeto e a arquitetura foram concebidos e modelados inicialmente na disciplina de **Análise e Projeto de Software (AL0332)**. Na disciplina atual de **Resolução de Problemas IV (AL0343)** do curso de **Engenharia de Software da Universidade Federal do Pampa (Unipampa - Campus Alegrete)**, a equipe consolidou a documentação técnica, a modelagem UML e o planejamento do MVP para guiar o ciclo de desenvolvimento e implementação do software.

---

## 📁 Estrutura do Repositório (Monorepo)

```
sgopi-sentinela/
├── backend/                       # API Python (FastAPI) — Arquitetura Hexagonal
│   ├── src/
│   │   ├── domain/                # Entidades, VOs e serviços de domínio puros (sem libs)
│   │   │   ├── ocorrencia/        # Ocorrencia (agregado), StatusOcorrencia + transições, eventos,
│   │   │   │                      # apreensão/custódia (extra RF03), autenticidade (extra RF08)
│   │   │   ├── viatura/           # Viatura, SituacaoViatura, Posicao
│   │   │   ├── despacho/          # OrdemDeDespacho, serviço de proximidade (Haversine)
│   │   │   ├── usuario/           # Usuario, Papel
│   │   │   ├── auditoria/         # RegistroAuditoria
│   │   │   ├── inquerito/         # Inquérito policial (extra RF06)
│   │   │   ├── laudo/             # Laudo pericial (extra RF07)
│   │   │   ├── medida_protetiva/  # Medida protetiva de urgência (extra RF09)
│   │   │   └── shared/            # Exceções (com chave i18n), Coordenada, CPF, documentos, eventos
│   │   ├── application/
│   │   │   ├── ports/inbound/     # Interface* + DTOs + Ator (um arquivo por caso de uso)
│   │   │   ├── ports/outbound/    # Repositorio*, UnidadeDeTrabalho, Relogio, GeradorProtocolo,
│   │   │   │                      # GeradorNumero*, PortaAuditoria, PublicadorEventos, HasherSenha,
│   │   │   │                      # ProvedorToken, ArmazenamentoArquivos
│   │   │   └── use_cases/         # auth/, ocorrencia/, viatura/, despacho/, auditoria/, usuario/,
│   │   │                          # inquerito/, laudo/, medida_protetiva/, documento/ (extras)
│   │   ├── adapters/
│   │   │   ├── inbound/http/      # deps (JWT/RBAC), erros, middleware, v1/*_router.py
│   │   │   ├── inbound/websocket/ # WS /v1/tempo-real + GerenciadorConexoes
│   │   │   ├── inbound/simulador/ # SimuladorTelemetria (driving adapter de GPS) + extras opcionais:
│   │   │   │                      # GeradorOcorrencias (demo) e OrquestradorDespacho
│   │   │   └── outbound/          # persistence/ (SQLAlchemy), seguranca/ (argon2, jose),
│   │   │                          # eventos/ (fan-out em memória), relogio/, arquivos/ (disco)
│   │   ├── infrastructure/
│   │   │   ├── config/            # Settings (pydantic-settings, .env)
│   │   │   ├── database/          # engine, models, migrations/ (Alembic)
│   │   │   ├── i18n/              # mensagens pt/en
│   │   │   ├── logging.py         # logs JSON com request_id + máscara de CPF
│   │   │   └── di.py              # Composition Root (única ponte portas ↔ adapters)
│   │   └── main.py                # criar_app(): middleware, handlers, routers, /health
│   ├── scripts/seed*.py           # Seed reproduzível (usuários, frota e 12 ocorrências fictícias)
│   ├── tests/                     # fakes/, unit/, integration/ (SQLite em memória), e2e/ (API real)
│   ├── alembic.ini · pyproject.toml · .env.example
├── frontend/                      # SPA React + TypeScript + Leaflet
│   ├── src/ {components, pages, services, hooks, types, utils, locales}
│   └── cypress/e2e/               # Testes E2E de interface (Cypress)
├── docs/
│   ├── DOCUMENTACAO_DE_ENGENHARIA.md · PLANEJAMENTO_DESENVOLVIMENTO.md · ROTEIRO_DEMONSTRACAO.md
│   ├── implementacao/             # Registros de etapas e complementos de implementação
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
uv run python -m scripts.seed   # usuários agente/delegado/operador (senha Senha@123) + 5 viaturas + 12 ocorrências

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
1. **Cidadão (Portal Público, sem login):** Acessa `http://localhost:3000/` com animação mecânica retrô via `<SplitFlapText />` → Clica em *Registrar Ocorrência* (`/registrar-cidadao`) → Preenche o fato e clica no mapa Leaflet para marcar a coordenada → Recebe o protocolo oficial `SGOPI-AAAA-NNNNNN` e acompanha o status em tempo real em `/consulta`.
2. **Delegado (Revisão & Triagem):** Clica em *Acesso Policial* (`/login`) e usa o atalho de demonstração da **Delegada** (`delegado` / `Senha@123`) → Acessa a *Fila de revisão* (`/fila`) → Identifica o registro do cidadão → Informa opcionalmente o **despacho da autoridade** e valida a ocorrência, gerando o hash SHA-256 da narrativa e preservando a decisão no histórico e na auditoria; nas decisões de devolução ou rejeição, informa a justificativa técnica obrigatória.
3. **Operador da Central (Despacho Tático):** Autentica-se como **Operador** (`operador` / `Senha@123`) → Acessa o *Painel tático* (`/painel`) → Ativa o *Simulador GPS* → Seleciona a ocorrência validada → *Despacha* uma das 3 viaturas mais próximas sugeridas pelo algoritmo de Haversine → *Encerra atendimento* com desfecho circunstanciado.

### Segurança (RNF02)

- **Login com proteção contra força bruta:** após `LOGIN_MAX_TENTATIVAS` falhas (padrão 5) do mesmo par login+IP em 15 min, o par fica bloqueado (HTTP 429 com `Retry-After`) e o bloqueio é auditado como `auth.login_bloqueado`. Tentativas negadas são auditadas **sem autor** (quem tentou é desconhecido); o usuário-alvo fica em `dados_depois.usuario_alvo_id`.
- **Delegacia Online com cota por IP:** `POST /v1/ocorrencias/publico` aceita até `REGISTRO_PUBLICO_MAX_POR_IP` comunicações (padrão 20) a cada 10 min por IP.
- **IP de origem confiável:** `X-Forwarded-For` só é considerado quando a conexão vem de `PROXIES_CONFIAVEIS` (padrão: loopback); sem isso, um cliente forjaria o IP para burlar limites e auditoria.
- **WebSocket sem token na URL:** o painel envia o JWT no cabeçalho `Sec-WebSocket-Protocol` (`["sgopi.bearer", <jwt>]`), e o servidor responde só `sgopi.bearer`. Token em query string é recusado (1008).
- **Consulta pública mínima (LGPD):** `GET /v1/ocorrencias/publico/{protocolo}` devolve apenas protocolo, status, natureza, localização e data; ocorrência excluída logicamente responde 404.

Os limites são configuráveis no `.env` (ver `backend/.env.example`). O limitador é em memória — adequado a uma instância da API; com réplicas, troque o adapter da porta `LimitadorTentativas`.

### Qualidade

<!-- Números da suíte: atualize SOMENTE esta tabela (demais documentos apontam para cá). -->
| Suíte | Situação atual |
| :--- | :--- |
| pytest (backend) | **744 testes** coletados — 731 unitários/integração + 13 E2E de API |
| Cobertura (`domain/` + `application/`) | **≈ 95 %** (meta ≥ 80 % no agregado; piso por arquivo: 85 % em `domain/`, 75 % em `application/`) |
| Vitest (frontend) | **7 testes** em 3 arquivos (`src/utils/__tests__`) |
| Cypress (frontend) | **36 testes** em 7 specs |

```bash
cd backend
uv run pytest -q                                   # unitários + integração + E2E de API (E2E é pulado se :8000 não responder)
uv run pytest --cov --cov-report=json              # cobertura ≥ 80 % em domain/ + application/
uv run python -m scripts.verificar_cobertura_por_arquivo   # piso de cobertura por arquivo
uv tool run ruff check src tests                   # lint estático
uv run alembic upgrade head && uv run alembic check          # modelos × migrações sem divergência

PYTHONPATH=src uv run lint-imports --config pyproject.toml   # contratos da Arquitetura Hexagonal
cd ../frontend && npx tsc --noEmit && npm test && npm run build && npm audit --omit=dev
```

### Testes E2E (Issues #21 e #22)

Pré-requisito: **backend** (`uv run uvicorn --app-dir src main:app --reload`) e **frontend** (`npm run dev`) rodando simultaneamente.

```bash
# Frontend (Cypress) — specs: registro, validacao-despacho, manchas, autenticar, apreensoes, auditoria
cd frontend
npm run e2e            # headless
npm run e2e:open       # interface gráfica do Cypress (ver "Visualização" abaixo)

# Backend (pytest E2E de API) — contra o servidor real em :8000
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
  No app: escolha *E2E Testing* → navegador (Chrome/Edge) → clique na spec desejada (`registro.cy.ts`, `validacao-despacho.cy.ts`, `manchas.cy.ts`, `autenticar.cy.ts`, `apreensoes.cy.ts` ou `auditoria.cy.ts`).  
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
| 🎭 **Roteiro de Demonstração** | [**docs/ROTEIRO_DEMONSTRACAO.md**](docs/ROTEIRO_DEMONSTRACAO.md) | Roteiro da apresentação final, setup pré-banca e dados semeados. |
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
- **Must Have (MVP Essencial — escopo canônico):** RF01 (Gestão de Ocorrência Policial), RF04 (Fluxo de Validação pelo Delegado) e RF02 (Monitoramento GPS e Despacho Tático).
- **Should Have (Alta Prioridade):** RF03 (Inventário de Apreensões), RF05 (Manchas Criminais e Alertas), RF07 (Laudos Periciais) — *implementados como extras*.
- **Could Have (Média Prioridade):** RF06 (Vinculação a Inquéritos), RF08 (Autenticação Pública de Documentos), RF09 (Medidas Protetivas) — *implementados como extras*.
- **Won't Have (Próximos Ciclos):** RF10 (Comunicação Interagências).

### ➕ Extras implementados (além do MVP)
Funcionalidades entregues **fora do escopo canônico do MVP** (RF01/RF04/RF02). Não redefinem o MVP:
- **RF03** — Inventário de apreensões com lacre único e cadeia de custódia *append-only*;
- **RF05** — Manchas criminais (*heatmap* por período e natureza) e banner de criticidade no painel tático;
- **RF06** — Inquéritos policiais com vinculação de ocorrências e sugestão de conexões;
- **RF07** — Laudos periciais com upload e verificação de integridade SHA-256;
- **RF08** — Autenticação pública de documentos por chave de segurança ou QR Code (`/autenticar`);
- **RF09** — Medidas protetivas com controle de vigência, renovação e revogação;
- **DEC-03** — Pin vetorial SVG animado nos formulários e no mapa;
- Arquivamento e exclusão lógica de ocorrência pelo Delegado; gerador de ocorrências fictícias para demonstração; orquestrador de despacho/encerramento automáticos (com viatura de apoio).

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
| Testes | pytest + pytest-asyncio · Cypress (E2E de interface) |
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
- **Testes E2E**: Cypress no frontend (fluxos do MVP e dos extras) e pytest E2E de API (HTTP + WebSocket) contra o servidor real — ver [Testes E2E](#testes-e2e-issues-21-e-22).

---

## 📐 Modelagem e Artefatos de Projeto

- Diagrama de Casos de Uso
- Diagrama de Pacotes (camadas hexagonais)
- Diagramas de Componentes (executável e hexagonal)
- Diagrama de Classes de Domínio
- Diagramas de Máquinas de Estados (Ocorrência e Viatura)
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
