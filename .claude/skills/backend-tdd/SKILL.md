---
name: backend-tdd
description: Roteiro de TDD para codificar no backend do SGOPI Sentinela (Python/FastAPI, arquitetura hexagonal) — entidades, casos de uso, portas, repositórios, routers e correção de bugs. Use ao implementar, alterar ou refatorar qualquer coisa em backend/.
---

# Backend com TDD

**Antes de tudo, leia o `AGENTS.md`**: camadas, diretórios, proibições e verificação estão lá e não se repetem aqui. Esta skill é o *como*: a ordem de trabalho e os padrões que o projeto já tem.

## Ciclo

Para cada comportamento, nesta ordem:

1. **Vermelho:** escreva o teste do comportamento e rode só ele; ele precisa **falhar pelo motivo certo** (asserção, não erro de import ou fixture). Em correção de bug, o teste reproduz o bug e é o teste de regressão.
2. **Verde:** escreva o mínimo de código que faz o teste passar.
3. **Refatorar:** com o teste verde, limpe (nomes, métodos < 35 linhas, reaproveitar os blocos abaixo) e rode de novo.
4. Ao fim do item, rode a suíte da área e depois a skill `verificar`.

Comandos (de `backend/`; `asyncio_mode = "auto"`, então teste async não precisa de decorator):

```bash
uv run pytest tests/unit/domain/test_<entidade>.py -q          # um arquivo
uv run pytest tests/unit -q -k "<trecho do nome>"               # por nome
uv run pytest -q -m "not e2e"                                   # suíte sem E2E
```

## De dentro para fora: um teste por camada

Comece pela camada mais interna que o comportamento toca. Só desça para a próxima quando a anterior estiver verde.

| Camada | Onde fica o teste | Como montar |
| :--- | :--- | :--- |
| Domínio (`domain/`) | `tests/unit/domain/test_<x>.py` | Sem fakes: crie a entidade pela fábrica (`Ocorrencia.registrar`, `MedidaProtetiva.conceder`, `Inquerito.instaurar`...) e passe instantes fixos `datetime(..., tzinfo=UTC)`. Erros: `pytest.raises(XError)` e confira `erro.value.chave`. |
| Caso de uso (`application/use_cases/`) | `tests/unit/use_cases/test_<x>.py` | Fakes compartilhados de `tests/fakes/` (abaixo) e atores de `tests/fakes/atores.py` (`AGENTE`, `OUTRO_AGENTE`, `DELEGADO`, `OPERADOR`). Confira estado salvo no fake, `AuditoriaFake.operacoes()`, eventos em `PublicadorEventosFake` e `UnidadeDeTrabalhoFake.commits`. |
| Persistência (`adapters/outbound/persistence/`) | `tests/integration/test_persistencia_<x>.py` | Fixtures `session`, `session_factory` e `usuarios` de `tests/integration/conftest.py` (SQLite em memória; `usuarios` devolve os ids de agente, delegado, operador, agente2, supervisor e perito). |
| HTTP (`adapters/inbound/http/`) | `tests/integration/test_<x>_http.py` | Fixture `client` e `tests/integration/helpers.py`: `auth(client, "delegado")` devolve os headers, `registrar(client, headers)` cria uma ocorrência. Confira status, `json()["code"]` (chave i18n) e o corpo. |
| Fluxo ponta a ponta | `tests/e2e/` | Contra a API real; rode pela skill `verificar` (completo). |

**Fakes de `tests/fakes/`:** `RelogioFake`, `GeradorProtocoloFake`, `UnidadeDeTrabalhoFake`, `AuditoriaFake`, `PublicadorEventosFake` (`portas_fake.py`), `RepositorioOcorrenciaFake`, `RepositorioViaturaFake`, `RepositorioMedidaProtetivaFake` + `GeradorNumeroMedidaFake`, `RepositorioNotificacaoFake`, `RepositorioOrdemDespachoFake`, fakes de autenticação (`auth_fake.py`).

- Precisa de uma fake que não existe? Crie em `tests/fakes/`, implementando **toda** a porta, devolvendo cópias (`copy.deepcopy`) e com a mesma ordenação e regras do adaptador SQL. Não declare fakes dentro do arquivo de teste.
- Repositório com `versao`: use `ControleVersaoFake` (`tests/fakes/controle_versao.py`) e acrescente o repositório à bateria de `tests/integration/contratos/` (fixtures `sessoes_fake`/`sessoes_sqlalchemy`, marcador `IMPLEMENTACOES`), que roda o mesmo teste contra a fake e contra o SQLAlchemy.

## Padrões do projeto (reaproveite, não reescreva)

- **Acesso:** `ator.exigir(Permissao.X, "mensagem", chave="dominio.chave")` no caso de uso e `Depends(exigir_permissao(Permissao.X))` no router. Ação nova entra em `domain/usuario/permissoes.py` e no teste `tests/unit/domain/test_permissoes.py`.
- **Auditoria:** `RegistroAuditoria(operacao=OperacaoAuditada.X, entidade=EntidadeAuditada.Y, ...)`; operação nova no catálogo (`domain/auditoria/catalogo.py`) no formato `dominio.acao`.
- **Transição de estado:** declare na tabela `MaquinaEstados` do agregado; o método da entidade consulta `proximo()`/`permite()` e lança o erro com a chave própria.
- **Mutação de entidade versionada:** termine com `self._tocar(instante)` (mixin `Versionado`).
- **Entrada da borda:** `exigir_texto(...)` para texto obrigatório/mínimo e `interpretar_enum(...)` para enum (valor inválido é recusado, não vira padrão).
- **Tempo:** instantes só pelo `Relogio` injetado (nunca `datetime.now` no domínio ou no caso de uso); data de calendário com `data_operacional(agora)`.
- **Erros:** sempre com `chave` i18n, e a mensagem nas duas traduções (`infrastructure/i18n/locales/{pt,en}/default.json`). O status HTTP sai do tipo da exceção (tabela em `adapters/inbound/http/erros.py`): `ConflitoError` → 409, `TransicaoInvalidaError`/`ValorInvalidoError`/`CampoObrigatorioError` → 422, `AcessoNegadoError` → 403, `EntidadeNaoEncontradaError` → 404.
- **Constantes:** regra fixa como constante de módulo junto da entidade; pesos/raios/janelas de heurística numa `@dataclass(frozen=True) Parametros...`; configuração de ambiente no `settings.py`.
- **Ligação:** adaptador novo só é instanciado em `infrastructure/di.py`; caso de uso recebe portas (ABCs) no construtor e expõe `executar(...)`.

## Pronto quando

- Cada comportamento novo tem teste que falhou antes do código; bug corrigido tem teste de regressão.
- Nenhum teste existente foi afrouxado; mudança intencional de comportamento está dita no commit.
- `verificar` verde; commit no padrão Conventional Commits; se for item do `docs/implementacao/PLANO_REFATORACAO_2026-11.md`, marque `[x]` com o hash.
