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
├── backend/                   # API Python (FastAPI) — Arquitetura Hexagonal
│   ├── src/
│   │   ├── domain/            # Entidades e regras de negócio puras (sem libs)
│   │   │   ├── ocorrencia/
│   │   │   └── shared/        # Exceções base do domínio
│   │   ├── application/
│   │   │   ├── ports/
│   │   │   │   ├── inbound/   # Contratos que os controllers implementam
│   │   │   │   └── outbound/  # Contratos que os repositórios implementam
│   │   │   └── use_cases/
│   │   │       └── ocorrencia/
│   │   ├── adapters/
│   │   │   ├── inbound/http/v1/   # Routers FastAPI (REST)
│   │   │   └── outbound/persistence/  # Implementações SQLAlchemy
│   │   ├── infrastructure/
│   │   │   ├── config/        # Settings (pydantic-settings)
│   │   │   └── database/      # Engine, sessão, migrations (Alembic)
│   │   └── main.py            # Composition Root / FastAPI app
│   ├── tests/
│   │   ├── fakes/             # Repositórios in-memory para testes unitários
│   │   ├── unit/              # Testes de domínio e use cases (sem banco)
│   │   └── integration/       # Testes com banco real
│   ├── db/
│   │   └── seed.sql           # Dados de teste compartilhados pela equipe
│   ├── .env.example           # Template de variáveis de ambiente
│   └── pyproject.toml
├── frontend/                  # SPA React + Leaflet (painel tático)
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/          # Clients HTTP e WebSocket
│   │   ├── hooks/
│   │   └── types/
│   ├── .env.example
│   └── package.json
├── docs/
│   ├── DOCUMENTACAO_DE_ENGENHARIA.md
│   ├── PLANEJAMENTO_DESENVOLVIMENTO.md
│   └── diagramas/
│       ├── sequencia/         # sq01-... a sq11-... (PNG)
│       └── *.png              # Casos de uso, classes, componentes, etc.
├── docker-compose.yml         # PostgreSQL local para desenvolvimento
└── README.md
```

> **Regra de ouro:** `domain/` e `application/` **nunca** importam FastAPI, SQLAlchemy ou qualquer lib externa. Apenas `adapters/` e `infrastructure/` podem.

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
cp .env.example .env
# Edite .env: deixe DATABASE_URL local descomentada

# 4. Rode o servidor
uv run uvicorn src.main:app --reload

# 5. Testes (sem banco)
uv run pytest tests/unit
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

---

## 📚 Documentação Técnica e Wiki

| Documento | Localização | Descrição |
| :--- | :--- | :--- |
| 📄 **Especificação Completa de Engenharia** | [**docs/DOCUMENTACAO_DE_ENGENHARIA.md**](docs/DOCUMENTACAO_DE_ENGENHARIA.md) | Requisitos (RF01–RF10, RNF01–RNF05), matriz MoSCoW, proposta de MVP, padrões de projeto e os 11 casos de uso com diagramas de sequência. |
| 🌐 **Wiki Oficial do Projeto** | [**GitHub Wiki**](https://github.com/rodrigothoma/sgopi-sentinela/wiki) | Base de conhecimento da equipe com guias, modelagem UML navegável e detalhamento arquitetural. |
| 📊 **Artefatos e Diagramas** | [**docs/diagramas/**](docs/diagramas/) | Todos os diagramas UML em alta definição. |

---

## 🎯 Proposta do MVP (Minimum Viable Product)

```
[ Agente Policial ] ──(Registro)──► [ Núcleo SGOPI ] ◄──(Revisão/Validação)── [ Delegado ]
                                            │
                                            ▼ (Status: Validada)
[ Viatura Policial ] ◄──(Despacho)── [ Operador Central (Mapa Tático GPS Real-Time) ]
```

### Matriz de Priorização (MoSCoW)
- **Must Have (MVP Essencial):** RF01 (Gestão de Ocorrência Policial), RF04 (Fluxo de Validação pelo Delegado), RF02 (Monitoramento GPS e Despacho Tático).
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

- **Desenvolvimento local:** Docker Compose sobe um PostgreSQL 16 com `seed.sql` compartilhado entre a equipe. Nenhum dado real é consumido.
- **Apresentação/Demo:** Supabase (PostgreSQL gerenciado). Basta comentar/descomentar a `DATABASE_URL` no `.env`.

---

## ⚙️ Estratégia de Qualidade

- **Testes unitários** (pytest): cobertura ≥ 80% sobre domínio e use cases — sem banco, sem servidor.
- **Testes de integração**: com banco real (via Docker ou Supabase).
- **Testes E2E** (Selenium): fluxos críticos do frontend.

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
