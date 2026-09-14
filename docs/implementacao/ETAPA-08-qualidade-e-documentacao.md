# ETAPA 08 — Qualidade, observabilidade e documentação (RNF05\*, RNF06, RNF09, RNF10, RNF12)

**Data:** 13/09/2026 · **Prioridade:** 🟡 (Sprint 5 — F3, T1 pendente, F5 parcial)

**Origem:** `ETAPA-04` §5 (RNF05\*, RNF06, RNF09, RNF10); `ETAPA-05` NEXT-15, NEXT-16, NEXT-17, NEXT-18 (parte do README); DIV-09, RNF-P07, RNF-P11, RNF-P16, HEX-13.

## 1. Objetivo

Tornar verificáveis as metas que a documentação declarava sem instrumento (cobertura ≥ 80 %, regra de ouro), fechar os itens de observabilidade e privacidade que faltavam, e alinhar o README ao que efetivamente roda.

## 2. O que foi implementado

| Item | Arquivo | Requisito |
| :--- | :--- | :--- |
| `pytest-cov` configurado com `source = domain + application`, `branch = true`, **`fail_under = 80`** | `backend/pyproject.toml` | RNF06, DIV-09 |
| **`import-linter`** com 3 contratos: `domain` não importa camadas nem libs; `application` só importa `domain`; camadas `adapters > infrastructure > application > domain` (exceção explícita: `infrastructure.di` = composition root) | `backend/pyproject.toml` `[tool.importlinter]` | RNF05\*, HEX-13 |
| Teste da regra de ouro na suíte (AST de todos os `.py` de `domain/` e `application/`) — 62 arquivos parametrizados | `tests/unit/test_regra_de_ouro.py` | RNF05\*, RNF-P16 |
| **Máscara de CPF em logs** (mensagem, campos extra, *stack trace*; formato pontuado e 11 dígitos) | `infrastructure/logging.py` | RNF10 |
| Teste do formatador JSON (`request_id`, `usuario_id`, `operacao`, máscara) | `tests/unit/adapters/test_logging.py` | RNF09, RNF10 |
| `.gitignore`: `.pytest_cache/`, `.coverage`, `htmlcov/`, `*.db` | raiz | RNF07 |
| **README** reescrito nas seções Estrutura, Como Rodar (Alembic + seed + fluxo de demo + qualidade), Documentação (link para esta pasta), MoSCoW (status), Banco e Qualidade | `README.md` | NEXT-18 (parcial), DIV-30 |
| Nota de base legal LGPD | `docs/implementacao/NOTA-LGPD-BASE-LEGAL.md` | RNF10, RNF-P11 |
| Índice consolidado com status por requisito e itens fora do escopo | `docs/implementacao/00-INDICE.md` | rastreabilidade |

## 3. Decisões tomadas durante a implementação

- A cobertura **não** foi adicionada ao `addopts` do pytest para manter o ciclo `uv run pytest` rápido; o comando com `--cov` está no README e é o que deve ir ao CI.
- `import-linter` exige `PYTHONPATH=src` porque o backend não é instalado como pacote (`[tool.uv] package = false`); comando documentado.
- A máscara de 11 dígitos só atua em sequências **exatamente** de 11 dígitos isoladas (evita mascarar telefones de 10 dígitos ou protocolos).
- `DOCUMENTACAO_DE_ENGENHARIA.md`, `PLANEJAMENTO_DESENVOLVIMENTO.md` e os diagramas **não foram alterados** — continuam sendo a tarefa F5 da Sprint 5 (NEXT-18); a fonte para essa atualização são as Etapas 1–7 desta pasta e a ETAPA-04 da análise.

## 4. Verificação

```
uv run pytest -q --cov          →  243 passed · cobertura domain+application = 98,58 % (fail_under 80)

PYTHONPATH=src uv run lint-imports --config pyproject.toml
                                →  Analyzed 134 files, 485 dependencies · Contracts: 3 kept, 0 broken
cd frontend && npx tsc --noEmit && npx vite build   →  OK
```

Arquivos com menor cobertura (todos ≥ 82 %): `domain/usuario/entity.py` (validações de campo), `domain/despacho/entity.py` (mensagens de exceção), `domain/shared/geo.py` (ramo NaN).

## 5. Fora desta etapa / dívidas registradas

- Testes E2E em navegador e medição de latência (ver [00-INDICE](00-INDICE.md) §"O que ficou fora").
- Pipeline de CI (GitHub Actions) executando `pytest --cov`, `lint-imports`, `tsc` e `vite build` — os comandos já estão prontos; falta o *workflow*.
- Atualização da Documentação de Engenharia e diagramas (F5).

## 6. Rastreabilidade

DIV-09 ✅ · RNF-P07 ✅ · RNF-P11 ✅ · RNF-P16 ✅ · HEX-13 ✅ · RNF05\* ✅ · RNF06 ✅ · RNF09 ✅ · RNF10 ✅ · NEXT-15 ✅ (exceto E2E) · NEXT-16 ✅ · NEXT-17 ✅ · NEXT-18 ◐ (README)
