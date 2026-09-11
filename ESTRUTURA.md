# Estrutura inicial — SGOPI Sentinela

Esqueleto da Arquitetura Hexagonal (Ports & Adapters), derivado dos
diagramas de pacotes e de componentes do projeto.

```
domain/                      → Entidades puras (sem framework nenhum)
application/
  ports/
    inbound/                 → Interfaces que os casos de uso expõem
    outbound/                → Interfaces que os casos de uso consomem
                                (repositórios, serviços externos)
  use_cases/                 → Regras de negócio / orquestração
adapters/
  inbound/                   → Controllers REST (FastAPI), WebSockets
  outbound/
    persistence/             → Implementações concretas dos repositórios
                                (SQLAlchemy)
infrastructure/               → Config de banco, variáveis de ambiente
tests/                         → Testes unitários (pytest) — usam fakes/mocks,
                                  nunca sobem servidor nem banco real
```

## O que já está implementado (RF01 — Must Have)

- `domain/ocorrencia.py` — entidade `Ocorrencia` com máquina de estados
  (REGISTRADA → EM_VALIDACAO → VALIDADA/REJEITADA).
- `application/ports/outbound/repositorio_ocorrencia.py` — porta de saída
  (interface abstrata do repositório).
- `application/ports/inbound/interface_registrar_ocorrencia_policial.py` —
  porta de entrada do caso de uso.
- `application/use_cases/registrar_ocorrencia_policial.py` — caso de uso
  que orquestra o registro de uma ocorrência.
- `tests/test_registrar_ocorrencia_policial.py` — testes unitários com
  repositório fake em memória (sem banco, sem servidor).

## Regra de ouro

`domain/` e `application/` **nunca** importam FastAPI, SQLAlchemy ou
qualquer outra lib externa. Só `adapters/` e `infrastructure/` podem.

## Próximos passos sugeridos

1. Implementar `adapters/outbound/persistence/ocorrencia_dao.py`
   (SQLAlchemy) implementando `RepositorioOcorrencia`.
2. Implementar `adapters/inbound/controle_ocorrencias_e_inqueritos.py`
   (rota FastAPI) chamando `RegistrarOcorrenciaPolicial`.
3. Ligar tudo em `main.py` via injeção de dependência do FastAPI
   (`Depends`).
4. Repetir o padrão para RF04 (validação pelo Delegado) e RF02
   (monitoramento GPS / despacho tático).

## Rodando

```bash
uv sync
uv run pytest
uv run uvicorn main:app --reload
```
