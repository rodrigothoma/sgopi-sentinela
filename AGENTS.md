# 🤖 Diretrizes para Agentes de IA e Desenvolvedores — SGOPI Sentinela

Este arquivo estabelece as regras canônicas de engenharia para qualquer **agente de IA** (Antigravity, Cursor, GitHub Copilot, Claude Code, etc.) ou **desenvolvedor** trabalhando no repositório **SGOPI Sentinela**.

---

## 1. 📖 Fonte Única da Verdade

1. **Documentação Oficial:** Toda implementação deve seguir estritamente o arquivo [`docs/DOCUMENTACAO_DE_ENGENHARIA.md`](docs/DOCUMENTACAO_DE_ENGENHARIA.md).
2. **Diagramas UML:** Antes de implementar ou alterar casos de uso, consulte obrigatoriamente os diagramas em [`docs/diagramas/`](docs/diagramas/) (especialmente os diagramas de sequência em `docs/diagramas/sequencia/`).
3. **Escopo Canônico do MVP:** Foco rigoroso nos requisitos **RF01** (Gestão de Ocorrência Policial), **RF04** (Validação pelo Delegado) e **RF02** (Monitoramento GPS e Despacho Tático). Não invente requisitos fora do escopo.

---

## 2. 🛠️ Stack Tecnológica Oficial (Proibido Alucinar Outras)

* **Backend:**
  * **Linguagem:** Python ≥ 3.13.
  * **Framework Web:** FastAPI (rotas REST e WebSockets nativos).
  * **Gerenciador:** `uv` (não utilize `pip` direto ou `poetry`).
  * **Banco de Dados:** PostgreSQL 16 (com suporte a SQLite em memória nos testes automatizados).
  * **ORM & Migrações:** SQLAlchemy 2.0 (async) e Alembic.
* **Frontend:**
  * **Linguagem & Framework:** React 18, TypeScript, Vite.
  * **Mapas:** Leaflet com tiles do OpenStreetMap.
  * **Comunicação em Tempo Real:** WebSockets nativos do FastAPI (JSON bidirecional).

---

## 3. 🏛️ Arquitetura Hexagonal (*Ports & Adapters*) — Regras Inegociáveis

A estrutura do backend em `backend/src/` segue divisão estrita validada por **`import-linter`**:

```text
backend/src/
├── domain/            # 1. CORE PURO: Regras de negócio invariantes
├── application/       # 2. CASOS DE USO: Orquestração do fluxo
├── ports/             # 3. CONTRATOS: Interfaces abstratas (Inbound e Outbound)
├── adapters/          # 4. TECNOLOGIA: HTTP, WebSockets, Repositórios SQLAlchemy
└── infrastructure/    # 5. CONFIGURAÇÃO: DI, engine de banco e logs
```

### 🚫 Proibições Estritas (A quebra falhará o build):
1. **`domain/` é Python Puro:**
   * **NUNCA** importe FastAPI, Starlette, SQLAlchemy, Pydantic, Alembic, Jose, Argon2 ou qualquer lib externa no `domain/`.
   * Entidades de domínio são **`dataclasses` padrão do Python** ou classes puras, nunca modelos de ORM nem schemas HTTP.
2. **`application/` só enxerga `domain/` e `ports/`:**
   * **NUNCA** acesse banco de dados diretamente dentro de um caso de uso.
   * **NUNCA** instancie adaptadores concretos (ex: `SQLAlchemyOcorrenciaRepository()`) no caso de uso. Toda dependência deve ser injetada via interface da porta (`ports/outbound/`).
3. **`ports/` define abstrações puras:**
   * Portas de entrada e saída devem herdar de `abc.ABC` com métodos `@abstractmethod`.
   * Use DTOs (dataclasses puras) para transporte entre camadas.
4. **`adapters/` implementa portas:**
   * `adapters/inbound/http/`: Usa FastAPI e Pydantic para validação na borda, traduz requisições para DTOs e chama casos de uso.
   * `adapters/outbound/persistence/`: Implementa as portas de repositório usando SQLAlchemy e converte entre modelos relacionais e entidades de domínio.
5. **Composition Root:**
   * O único arquivo autorizado a instanciar adaptadores e injetá-los nos casos de uso é o [`backend/src/infrastructure/di.py`](backend/src/infrastructure/di.py).

---

## 4. 💎 Princípios SOLID & Clean Code Obrigatórios

* **S — Single Responsibility Principle (SRP):**
  * Cada caso de uso deve ter **uma única responsabilidade** e expor um método principal `execute(...)`.
  * Métodos e funções devem ser curtos (< 35 linhas) e com objetivo claro.
* **O — Open/Closed Principle (OCP):**
  * Novas regras e comportamentos devem ser adicionados através de novas implementações de portas ou novos casos de uso, sem modificar código estável.
* **L — Liskov Substitution Principle (LSP):**
  * Adaptadores substitutos (ex: repositório em memória para testes e repositório PostgreSQL para produção) devem honrar 100% dos contratos das portas sem lançar exceções inesperadas.
* **I — Interface Segregation Principle (ISP):**
  * Portas devem ser coesas e específicas (`PortaAuditoria`, `PortaGPS`, `RepositorioOcorrencia`), evitando interfaces "gordas" com métodos desnecessários.
* **D — Dependency Inversion Principle (DIP):**
  * Módulos de alto nível (`application`) nunca dependem de módulos de baixo nível (`adapters`). Ambos dependem de abstrações (`ports`).
* **Clean Code:**
  * Nomenclatura expressiva e semântica (em português para o domínio policial, seguindo o padrão já estabelecido: `numero_protocolo`, `viatura_id`, `relato`, etc.).
  * Não comente código óbvio. Preserve docstrings informativas e tipagem explícita em todos os parâmetros e retornos.
  * Não use números mágicos nem strings literais espalhadas (use Enums e constantes de domínio).

---

## 5. 🛡️ Imutabilidade e Auditoria (RNF03)

* **Sem Deleções Físicas:** Nunca execute `DELETE` em tabelas de negócio (`ocorrencias`, `viaturas`, `evidencias_digitais`). Utilize exclusão lógica (`ativo = false`).
* **Tabelas Append-Only:** As tabelas `registros_auditoria` e `historico_status_ocorrencia` são estritamente incrementais. Jamais execute `UPDATE` ou `DELETE` nelas.
* **Integridade Criptográfica:** Toda ocorrência validada deve computar e registrar seu `hash_narrativa` (SHA-256) imutável.

---

## 6. 🧪 Verificação Obrigatória Antes de Concluir Tarefas

Todo agente ou desenvolvedor deve rodar e garantir que os comandos abaixo passam **sem nenhum erro**:

```bash
# 1. Contratos da Arquitetura Hexagonal (Zero violações permitidas)
cd backend && PYTHONPATH=src uv run lint-imports --config pyproject.toml

# 2. Suíte de Testes com Cobertura >= 80% em domain/ e application/
uv run pytest --cov

# 3. Tipagem e Build do Frontend
cd ../frontend && npx tsc --noEmit && npm run build
```

---

## 7. 🚫 Higiene de Saída de IA

* **NUNCA** inclua artefatos de chat de LLM (`contentReference`, notas de prompt, etc.) em arquivos de código ou documentação.
* Commits devem seguir rigorosamente o padrão **Conventional Commits** (`feat(escopo): ...`, `fix(escopo): ...`, `docs(escopo): ...`).
