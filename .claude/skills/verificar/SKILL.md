---
name: verificar
description: Roda a verificação equivalente ao CI do SGOPI Sentinela (import-linter, ruff, migrações, testes com E2E e cobertura, tsc, Vitest, build e npm audit) e corrige o que falhar. Use antes de commitar, abrir PR, enviar para a dev ou declarar uma tarefa concluída.
argument-hint: "[--rapido]"
---

# Verificação local (= CI)

1. Rode na raiz do repositório:
   - `./scripts/verificar.sh` — completo, o mesmo que `.github/workflows/ci.yml` (exceto o job de migrações no PostgreSQL). Leva cerca de 1 min e meio.
   - `./scripts/verificar.sh --rapido` — se o usuário pediu `--rapido` ou se é uma checagem intermediária: arquitetura, ruff, testes sem E2E e tsc.
2. O resumo final lista as etapas que falharam. Para cada uma, leia a saída da etapa e corrija a **causa**:
   - **import-linter:** uma camada importou o que não podia (AGENTS.md §3). Mova o código para a camada certa; não acrescente exceção ao contrato.
   - **ruff:** `cd backend && uv tool run ruff check --fix src tests` resolve ordem de imports e imports sem uso; o resto se corrige à mão.
   - **Migrações (`alembic check`):** modelo alterado sem migração. Crie a migração em `backend/src/infrastructure/database/migrations/versions/`.
   - **Testes:** nunca afrouxe asserções nem apague testes para passar. Se a mudança de comportamento foi intencional, atualize o teste e diga isso ao usuário.
   - **Cobertura por arquivo:** escreva os testes que faltam no arquivo apontado (pisos em `backend/scripts/verificar_cobertura_por_arquivo.py`).
   - **npm audit:** `cd frontend && npm audit fix` (sem `--force`); confira que só o `package-lock.json` mudou.
3. Rode de novo até ficar verde. Não use `git commit --no-verify` para contornar o pre-commit.
4. Responda com o resultado de cada etapa (números de testes e cobertura) e o que foi corrigido.
