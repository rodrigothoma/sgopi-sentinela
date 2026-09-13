# 📋 Análise de Requisitos e Prontidão do MVP — Índice e Método

**Projeto:** SGOPI Sentinela
**Data da análise:** 13/09/2026
**Branch analisada:** `matheus-Fastapi` (commit `38157c0`)
**Escopo do prompt que originou esta análise:**

> Analisar os documentos em `/docs` e o `README.md`, identificar problemas nos requisitos funcionais e não funcionais, verificar a necessidade de novos requisitos para que um MVP possa ser criado seguindo a Arquitetura Hexagonal, particionar a execução em etapas rastreáveis (um markdown por etapa), deixando explícito o que foi encontrado, o que ficou fora do escopo e sugestões de próximas implementações.

---

## Estrutura desta pasta

| Etapa | Arquivo | O que contém |
| :---: | :--- | :--- |
| 0 | `00-INDICE-E-METODO.md` (este) | Escopo, método, insumos lidos, convenções de IDs |
| 1 | [`ETAPA-01-inventario-e-divergencias.md`](ETAPA-01-inventario-e-divergencias.md) | Inventário do que foi lido e catálogo de divergências **doc × doc** e **doc × código** |
| 2 | [`ETAPA-02-analise-requisitos-funcionais.md`](ETAPA-02-analise-requisitos-funcionais.md) | Problemas em RF01–RF10 e nos UC01–UC12 |
| 3 | [`ETAPA-03-analise-requisitos-nao-funcionais.md`](ETAPA-03-analise-requisitos-nao-funcionais.md) | Problemas em RNF01–RNF05 e RNFs ausentes |
| 4 | [`ETAPA-04-novos-requisitos-mvp-hexagonal.md`](ETAPA-04-novos-requisitos-mvp-hexagonal.md) | Requisitos novos/reescritos necessários ao MVP, com mapeamento em portas/adaptadores e gap do código atual |
| 5 | [`ETAPA-05-consolidacao-escopo-e-proximos-passos.md`](ETAPA-05-consolidacao-escopo-e-proximos-passos.md) | Consolidação: encontrado / fora de escopo / próximas implementações sugeridas, com ordem recomendada |

Cada arquivo de etapa termina com a seção **"O que foi feito nesta etapa"**, que registra as ações executadas e os artefatos gerados, para rastreabilidade.

---

## Insumos analisados

### Documentos textuais
- `README.md` (raiz)
- `docs/DOCUMENTACAO_DE_ENGENHARIA.md` (seções 1 a 7)
- `docs/PLANEJAMENTO_DESENVOLVIMENTO.md` (Sprints 2–5)

### Diagramas (lidos visualmente)
- `diagrama-casos-de-uso.png`
- `diagrama-classes-dominio.png`
- `diagrama-pacotes-arquitetura-hexagonal.png`
- `diagrama-componentes-modulos-hexagonal.png`
- `diagrama-componentes-versao-executavel.png`
- `diagrama-implantacao-arquitetura-hexagonal.png`
- `mapeamento-relacional.png`
- `sequencia/sq01`, `sq02`, `sq04` (os três do escopo do MVP, lidos em detalhe)
- `sequencia/sq03, sq05–sq11` (não lidos em detalhe — fora do escopo do MVP; ver Etapa 5)

### Código (para cruzar documentação × implementação)
- `backend/src/**` (domínio, portas, caso de uso, adapters, infraestrutura, i18n)
- `backend/tests/**` (executados: **15 passed**)
- `backend/pyproject.toml`, `backend/.env.example`, `backend/db/seed.sql`
- `frontend/src/**`, `frontend/package.json`
- `docker-compose.yml`, `.gitignore`, histórico `git log`

---

## Método

1. **Leitura integral** dos documentos e dos diagramas; leitura do código existente.
2. **Cruzamento em três eixos**: (a) documento × documento (README × Doc. Engenharia × Planejamento × diagramas); (b) documento × código; (c) requisito × Arquitetura Hexagonal (existe porta/caso de uso/adaptador que o realize?).
3. **Critérios de avaliação de cada requisito** (baseados em ISO/IEC/IEEE 29148): *atômico*, *não ambíguo*, *verificável/mensurável*, *completo*, *consistente com os demais*, *rastreável* (a UC, diagrama e código).
4. **Classificação de severidade** dos achados:
   - 🔴 **Bloqueante** — impede o MVP (§3 da Doc. de Engenharia) de ser construído ou demonstrado como descrito.
   - 🟠 **Alto** — gera retrabalho ou erro de lógica se não for resolvido antes da sprint que o toca.
   - 🟡 **Médio** — inconsistência que confunde a equipe, mas não bloqueia.
   - ⚪ **Baixo** — cosmético / editorial.
5. **Registro de decisões de escopo**: tudo que foi identificado mas não tratado está listado na Etapa 5.

---

## Convenções de identificadores usados nesta análise

| Prefixo | Significado | Exemplo |
| :--- | :--- | :--- |
| `DIV-nn` | Divergência entre artefatos (Etapa 1) | `DIV-03` |
| `RF-Pnn` | Problema em requisito funcional (Etapa 2) | `RF-P07` |
| `RNF-Pnn` | Problema em requisito não funcional (Etapa 3) | `RNF-P02` |
| `RFnn` (11+) | **Novo** requisito funcional proposto (Etapa 4) | `RF13` |
| `RNFnn` (06+) | **Novo** requisito não funcional proposto (Etapa 4) | `RNF07` |
| `HEX-nn` | Lacuna de aderência à Arquitetura Hexagonal no código atual (Etapa 4) | `HEX-04` |
| `NEXT-nn` | Sugestão de próxima implementação (Etapa 5) | `NEXT-02` |

> **Importante:** esta análise **não altera** `DOCUMENTACAO_DE_ENGENHARIA.md`, `PLANEJAMENTO_DESENVOLVIMENTO.md`, os diagramas nem o código. Ela produz apenas os arquivos desta pasta (e uma linha de link na tabela de documentação do `README.md`). As correções propostas ficam como recomendações para a equipe decidir (ver Etapa 5).
