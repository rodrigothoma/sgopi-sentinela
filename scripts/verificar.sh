#!/usr/bin/env bash
# Verificação local equivalente ao CI (.github/workflows/ci.yml) — AGENTS.md §6.
#
#   ./scripts/verificar.sh            # completo: o mesmo que o CI roda (exceto o job do PostgreSQL)
#   ./scripts/verificar.sh --rapido   # arquitetura, ruff, testes sem E2E e tsc (~1 min)
#
# O completo usa um banco SQLite temporário e sobe a API numa porta livre para os testes
# E2E em modo estrito; nada toca o banco local nem o .env.
set -uo pipefail

RAPIDO=0
[ "${1:-}" = "--rapido" ] && RAPIDO=1

RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
PID_API=""
falhas=()

limpar() {
  [ -n "$PID_API" ] && kill "$PID_API" 2>/dev/null
  rm -rf "$TMP"
}
trap limpar EXIT

etapa() { printf '\n\033[1;34m==> %s\033[0m\n' "$1"; }
executar() {  # executar "nome da etapa" comando...
  local nome="$1"; shift
  etapa "$nome"
  if ! "$@"; then
    falhas+=("$nome")
    printf '\033[31m✗ %s\033[0m\n' "$nome"
  fi
}

subir_api() {
  local porta
  porta="$(python3 -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1])')"
  export SGOPI_E2E_BASE_URL="http://127.0.0.1:$porta" SGOPI_E2E_STRICT=1
  uv run uvicorn --app-dir src main:app --host 127.0.0.1 --port "$porta" >"$TMP/api.log" 2>&1 &
  PID_API=$!
  for _ in $(seq 1 30); do
    curl -fs "$SGOPI_E2E_BASE_URL/health" >/dev/null 2>&1 && return 0
    sleep 1
  done
  echo "API não subiu; log:" && cat "$TMP/api.log"
  return 1
}

preparar_banco() {
  uv run alembic upgrade head >/dev/null &&
    uv run alembic check &&
    uv run python -m scripts.seed >/dev/null
}

testes_backend() {
  if [ "$RAPIDO" -eq 1 ]; then
    uv run pytest -q --cov --cov-report=term:skip-covered -m "not e2e"
  else
    uv run pytest -q --cov --cov-report=term:skip-covered --cov-report="json:$TMP/coverage.json" &&
      uv run python -m scripts.verificar_cobertura_por_arquivo "$TMP/coverage.json"
  fi
}

residuos_ia() {
  local marcador="content""Reference"  # em partes, para este script não acusar a si mesmo
  ! grep -rn "$marcador" docs/ backend/src/ frontend/src/
}

# ------------------------------------------------------------------ backend
cd "$RAIZ/backend" || exit 1
export DATABASE_URL="sqlite+aiosqlite:///$TMP/sgopi_ci.db"
executar "Contratos da arquitetura hexagonal (import-linter)" env PYTHONPATH=src uv run lint-imports --config pyproject.toml
executar "Lint estático (ruff)" uv tool run ruff check src tests
if [ "$RAPIDO" -eq 0 ]; then
  executar "Migrações (upgrade + check) e seed" preparar_banco
  executar "API para os testes E2E" subir_api
fi
executar "Testes e cobertura" testes_backend

# ----------------------------------------------------------------- frontend
cd "$RAIZ/frontend" || exit 1
[ -d node_modules ] || executar "Dependências do frontend (npm ci)" npm ci
executar "Tipos do frontend (tsc)" npx --no-install tsc --noEmit
if [ "$RAPIDO" -eq 0 ]; then
  executar "Testes do frontend (Vitest)" npm test --silent
  executar "Build de produção (Vite)" npm run build --silent
  executar "Auditoria de dependências de produção" npm audit --omit=dev --audit-level=high
fi

cd "$RAIZ" || exit 1
executar "Resíduos de chat de IA" residuos_ia

# ------------------------------------------------------------------ resumo
echo
if [ "${#falhas[@]}" -eq 0 ]; then
  printf '\033[1;32m✓ Tudo verde%s.\033[0m\n' "$([ "$RAPIDO" -eq 1 ] && echo ' (modo rápido: sem E2E, build e auditoria)')"
  exit 0
fi
printf '\033[1;31m✗ %d etapa(s) com falha:\033[0m\n' "${#falhas[@]}"
printf '  - %s\n' "${falhas[@]}"
exit 1
