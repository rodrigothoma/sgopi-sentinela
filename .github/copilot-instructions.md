# GitHub Copilot Custom Instructions — SGOPI Sentinela

All code generated for this repository must strictly adhere to the guidelines established in `AGENTS.md` and `docs/DOCUMENTACAO_DE_ENGENHARIA.md`.

## Core Architectural Constraints
1. **Hexagonal Architecture:**
   - `backend/src/domain/`: Pure standard library Python only. Absolutely no imports from FastAPI, SQLAlchemy, Pydantic, or external packages.
   - `backend/src/application/`: Orchestration use cases. Only interacts with `ports/` interfaces. No concrete adapters or direct DB access.
   - `backend/src/ports/`: Abstract contracts (`abc.ABC`) and plain DTOs.
   - `backend/src/adapters/`: Inbound HTTP routes (FastAPI/Pydantic) and outbound persistence (SQLAlchemy).
   - `backend/src/infrastructure/di.py`: The single composition root for dependency injection.

2. **SOLID & Clean Code:**
   - Single Responsibility: One responsibility per use case class (`execute()`).
   - Dependency Inversion: Depend on abstractions (`ports/`), never on details (`adapters/`).
   - Strict typing across all signatures.
   - No dead code, no placeholder comments, no AI chat artifacts.
   - Append-only tables: `registros_auditoria` and `historico_status_ocorrencia` never accept `UPDATE` or `DELETE`.

3. **Validation Commands:**
   - `PYTHONPATH=src uv run lint-imports --config pyproject.toml`
   - `uv run pytest --cov` (coverage >= 80%)
   - `npm run build` in `frontend/`
