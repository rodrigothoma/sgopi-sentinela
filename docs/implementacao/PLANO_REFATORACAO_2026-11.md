# Plano de Refatoração — SGOPI Sentinela (novembro/2026)

**Situação em 08/11/2026:** Ondas 0 e 1 concluídas e integradas na `dev` (CI verde nos 3 jobs). Ondas 2 a 5 pendentes.

**Legenda:** `[x]` concluído (com o commit) · `[~]` parcial · `[ ]` pendente.

Caminhos do backend são relativos a `backend/src/`; os do frontend, a `frontend/src/`. A comparação completa do que já foi feito está em [`2b07f82...26da69e`](https://github.com/rodrigothoma/sgopi-sentinela/compare/2b07f82...26da69e).

---

## 1. Ponto de partida e progresso

| Métrica | Antes (06/11) | Agora (08/11) | Onde |
| :--- | :--- | :--- | :--- |
| Checagens de papel escritas à mão (`if ator.papel ...`) | 15 | 0 | casos de uso |
| Tuplas de papéis duplicadas entre routers e casos de uso | 20+ | 0 | `adapters/inbound/http/v1/*`, casos de uso |
| Strings soltas de auditoria (`operacao=`/`entidade=`) | 39 pontos | 0 | casos de uso, `deps.py` |
| Incrementos manuais `versao += 1` | 12 | 0 | entidades |
| Validações de texto vazio/curto repetidas | 28 | 0 | entidades |
| Testes do backend | 831 + 13 E2E | 926 + 13 E2E | `backend/tests/` |
| Cobertura (`domain/` + `application/`) | 95,4% | 96,7% | — |
| Tamanho do composition root | 1164 linhas | 1164 linhas | `infrastructure/di.py` (Onda 3) |
| Maior página do frontend | 1362 linhas | 1362 linhas | `pages/InqueritosPage.tsx` (Onda 4) |
| Repositórios ainda sem Mapper | 8 | 8 | `adapters/outbound/persistence/` (Onda 3) |

### Padrão para constantes e parâmetros

Nem toda constante vira dataclass. O critério é o tipo de valor:

| Tipo de valor | Exemplo | Onde fica |
| :--- | :--- | :--- |
| Regra fixa do negócio (lei, invariante) | `PRAZO_MAXIMO_DIAS = 730`, `TAMANHO_MINIMO_EMENTA` | Constante de módulo ao lado da entidade (padrão atual) |
| Parâmetros de uma heurística, ajustados em conjunto | Pesos, raios e janelas do motor de conexões e das áreas de risco | `@dataclass(frozen=True) Parametros...` no domínio, com os valores padrão e injetável no caso de uso |
| Configuração operacional (varia por ambiente) | Intervalos e velocidades do simulador, limites de tentativas | `infrastructure/config/settings.py`, injetado pelo `di.py` (sem repetir o padrão no construtor) |
| Fator de unidade ou de algoritmo | Metros por km, tamanho do SHA-256, dígitos do CPF | Constante única em `domain/shared` (ou no módulo do algoritmo) |

Levantamento de 08/11 (varredura de constantes e números soltos no backend):

| Arquivo | Situação | Destino |
| :--- | :--- | :--- |
| `application/use_cases/inquerito/buscar_conexoes.py` | 29 constantes de pesos, limiares, raios e janelas | `ParametrosMotorConexoes` (Onda 2) |
| `application/use_cases/inteligencia/calcular_areas_risco.py` | Números soltos: raio 1200 m, mínimo de 2 ocorrências em 24 h ou 3 em 7 dias, raio entre 350 e 1500 m, folga de 150 m, `CRITICA` com 3+, limite de 500 | `ParametrosAreasRisco` (Onda 2) |
| Motor de conexões, áreas de risco, `simulador/navegacao.py`, `simulador/simulador_telemetria.py` | Fator `1000` (metros por km) repetido | `METROS_POR_KM` e `Coordenada.distancia_metros()` em `domain/shared/geo.py` (Onda 2) |
| `adapters/inbound/simulador/*` | Já configurado pelo `settings.py`, mas os construtores repetem os padrões e um diverge (passo até o destino: 300 m no construtor, 35 m no settings) | Construtores sem padrão próprio, valores só no settings (Onda 3) |
| `domain/ocorrencia/entity.py`, `domain/laudo/entity.py` | Tamanho do SHA-256 (`64`) fixo no código | `TAMANHO_HASH_SHA256` em `domain/shared` (Onda 2) |
| `application/use_cases/medida_protetiva/emitir_alerta_vencimento.py` | `limit=500` na varredura | Constante `LIMITE_VARREDURA` (Onda 2) |
| `adapters/inbound/http/erros.py`, `main.py`, `domain/shared/documentos.py`, `domain/shared/geo.py` | Códigos HTTP, dígitos do CPF, limites de latitude/longitude | Aceitáveis como estão |

---

## 2. Onda 0 — Bugs e segurança ✅

- [x] **Sigilo de ofícios não era verificado.** A consulta ignorava o ator; agora filtra por nível de sigilo e papel, e a resposta a ofício sem acesso responde 404. — `afe0f61`
- [x] **Sigilo vazava por notificações e WebSocket** *(encontrado durante a correção)*. Notificação por departamento ia para todos os usuários com o assunto do ofício; o evento de tempo real chegava a papéis sem acesso. — `2cd61e6`
- [x] **Frontend enviava `RESTRITO`**, valor inexistente no backend: todo ofício marcado "Restrito" era gravado como público *(encontrado durante a correção)*. — `8bc04d6`
- [x] **Data em UTC nas medidas protetivas.** `agora.date()` adiantava o dia entre 21h e 24h; agora usa `data_operacional`. — `fe5dccc`
- [x] **Listagem de ofícios perdia registros.** Filtro de departamento rodava em Python depois do `LIMIT`; foi para o SQL. — `afe0f61`
- [x] **Corrida na numeração de ofícios.** SELECT FOR UPDATE + insert trocado pelo UPSERT dos demais geradores. — `17eda28`
- [x] **Permissão de consulta de inquéritos divergente** entre frontend, router e caso de uso. Regra única: Delegado, Supervisor e Operador Central. — `a93a08b`
- [x] **Falha silenciosa e relógio no domínio.** `except Exception: return []` passou a registrar log; `datetime.now` saiu dos `default_factory`. — `bd3d83a`
- [x] **Fakes fora do contrato (LSP).** `ControleVersaoFake` replica a regra do SQLAlchemy; `tests/integration/contratos/` roda a mesma bateria contra fake e SQL. — `302eccf`
- [x] **Auditoria de dependências do CI** (`follow-redirects` com alerta de severidade alta). — `e96de24`

---

## 3. Onda 1 — Fundações de domínio ✅

- [x] **Permissões centralizadas.** `domain/usuario/permissoes.py` (`Permissao` → papéis), `ator.exigir(...)` nos casos de uso e `exigir_permissao(...)` nos routers e no WebSocket. — `2f254c1`
- [x] **Catálogo de auditoria.** `domain/auditoria/catalogo.py` (`OperacaoAuditada`, `EntidadeAuditada`, `grafias()` para os registros legados). — `79b5a8d`
- [x] **Máquina de estados genérica.** `domain/shared/maquina_estados.py`; Ocorrência (`OperacaoOcorrencia`), Viatura, Inquérito e Medida declaram suas transições. — `de2b4fe`
- [x] **Mixin `Versionado`.** `domain/shared/versionado.py` com `_tocar(instante)` nas 5 entidades versionadas. — `de2b4fe`
- [x] **Helpers de validação e enum.** `domain/shared/validacao.exigir_texto` e `domain/shared/enums.interpretar_enum`; mínimos viraram constantes `TAMANHO_MINIMO_*`. — `8b281d1`
- [x] **Regras de volta às entidades.** `Ocorrencia.exigir_vinculavel()` (`de2b4fe`), `Ocorrencia.exigir_despachavel()` e `MedidaProtetiva.precisa_alerta()` (`904d547`).
- [~] **Enums e constantes.** Feito: escala única `domain/shared/prioridade.Prioridade`, Haversine reaproveitado, `SinalViatura`, `TipoRestricao` validado, prazos nomeados (`b97f3aa`). **Pendente:** tipar com enum `departamento_origem` e `papel_destinatario`, que mexem em DTOs e persistência (vai para a Onda 3).
- [x] **Enxugar `Ocorrencia`.** Canonicalização do hash extraída para `domain/ocorrencia/hash_narrativa.py`, com uma estratégia por versão. — `e7daa55`

### Mudanças de comportamento introduzidas (para o time saber)

- Operador, Escrivão, Agente e Perito não veem mais ofícios `CONFIDENCIAL`; Agente e Perito também não veem `RESERVADO`. Ofício restrito gera uma notificação por papel autorizado.
- Sigilo, prioridade ou tipo de restrição inválidos respondem 422, em vez de assumir o valor padrão.
- Cinco operações de auditoria mudaram de nome nos registros novos (ex.: `ENVIO_COMUNICACAO_INTERAGENCIAS` → `interagencias.enviar`); registros antigos mantêm a grafia.
- Ofícios gravados como públicos pelo bug do "Restrito" continuam públicos no banco (não há como identificá-los).

---

## 4. Onda 2 — Camada de aplicação

- [ ] **`application/use_cases/_base.py` com `ComandoAuditado[E](ABC)`** (Template Method: papel → carregar → aplicar → salvar → auditar → commit → saída). Promover `_DecisaoBase` (`revisar_ocorrencia.py`) e `_GestaoBase` (`gerir_usuarios.py`); aplicar em renovar/revogar medida, laudos e inquéritos.
- [ ] **`obter_ou_falhar(busca, id, chave)` genérico** no lugar de `carregar_ou_404` (8 importadores) e `carregar_viatura`; `_comum.py` por pacote, acabando com os imports cruzados entre casos de uso.
- [~] **`_mapeadores.py` por pacote**: `LaudoOutput` centralizado e coberto por testes de caracterização — `99e248d`. **Pendentes:** `MedidaProtetivaOutput` (4 montagens), `InqueritoOutput` (3) e `OcorrenciaResumoInqueritoOutput` (5).
- [ ] **Alinhar notificação, interagências, inteligência e alerta ao padrão**: UoW obrigatório (8 `uow | None`), Output DTOs no lugar de `dict`/entidades (12 portas), nomes sem sufixo `UseCase`, `chave` em todas as exceções.
- [ ] **Motor de conexões** (`inquerito/buscar_conexoes.py`, 421 linhas):
    - [ ] Mover a lógica pura para `domain/inquerito/motor_conexoes.py` com Strategy (`CriterioConexao`: envolvidos, natureza, tipificação, itens, área de risco, proximidade, temporal).
    - [ ] **Agrupar as 29 constantes** (`PESO_*`, `TAMANHO_MINIMO_*`, raios, janelas, `PONTUACAO_MINIMA`) numa `@dataclass(frozen=True) ParametrosMotorConexoes`, injetável no motor: os pesos ficam num objeto só, documentado e variável nos testes (ver *Padrão para constantes e parâmetros*).
    - [ ] **Revisar `FAMILIAS_CRIMINAIS`**: a comparação por substring coloca "DISPARO DE ARMA" em duas famílias; "HOMICIDIO CULPOSO" (ex.: acidente de trânsito) cai no grupo de crimes violentos; entradas como "ROUBO DE VEICULO" são redundantes com "ROUBO".
    - [ ] Trocar `list[dict]` das áreas de risco por um dataclass `AreaRisco`.
    - [ ] Devolver `motivos` estruturados (`{tipo, params}`) para o frontend traduzir (desbloqueia os badges da Onda 4).
    - [ ] Reaproveitar `normalizar_cpf` e `domain/shared/tempo` no lugar de `_limpar_documento` e `_para_utc`.
- [ ] **Áreas de risco com parâmetros nomeados**: `ParametrosAreasRisco` (raio de agrupamento, mínimos por janela, faixa de raio, folga, limiar de criticidade, limite de varredura) e serviço de domínio de manchas no lugar do agrupamento O(n²) dentro do caso de uso.
- [ ] **Fatores únicos em `domain/shared`**: `METROS_POR_KM` + `Coordenada.distancia_metros()` (fator repetido em 4 arquivos) e `TAMANHO_HASH_SHA256` (evidência e laudo); `LIMITE_VARREDURA` no alerta de vencimento.
- [ ] **Decompor as funções longas**: `_processar_alerta_medida` (103 linhas; HTML do e-mail vai para um adapter), `gerir_comunicacoes.executar` (97), `instaurar_inquerito` (86), `calcular_areas_risco.executar` (85), `solicitar_laudo` (80), `anexar_laudo` (77), `conceder_medida` (75).
- [ ] **Portas**: um único `GeradorNumeroSequencial` com enum de prefixos (hoje 6 portas); remover métodos abstratos sem uso; padronizar `Input`/`dados`/`buscar_por_id`/paginação `limit/offset`; remover o `UsuarioOutput` duplicado.

---

## 5. Onda 3 — Adapters e infraestrutura

- [ ] **Repositório base versionado** `RepositorioVersionadoSQLAlchemy[M, E]` para os 5 repositórios que copiam o controle de versão.
- [ ] **Mappers** para medida_protetiva, laudo, inquerito, comunicacao, notificacao, ordem_despacho, usuario e auditoria (padrão de `persistence/mappers/`); helpers `aware_opcional()` e `enum_ou_padrao()`.
- [ ] **`GeradorSequencialSQLAlchemy(tabela, formatador)`** no lugar dos 6 UPSERTs idênticos.
- [ ] **Routers**: schemas em `http/schemas/`, conversores em `conversores.py` (sem import entre routers), `ConfigDict(from_attributes=True)`, `Pagina[T]` genérico; regra de negócio fora de `viaturas_router`, `laudos_router` (validação de upload) e `inqueritos_router` (`split(' · ')`).
- [ ] **Dividir o `di.py` (1164 linhas)** em `infrastructure/providers/*`, com `ContextoSessao` no lugar das tuplas posicionais e singletons no `lifespan`.
- [ ] **Novos contratos no import-linter**: http ↛ simulador, outbound ↛ inbound, routers ↛ routers.
- [ ] **Performance**: `listar_resumos()` com projeção na exportação de ocorrências; ids de inquérito sem carregar ocorrências inteiras.
- [ ] **Configuração**: segredos como `SecretStr`.
- [ ] **Simulador sem padrões duplicados**: construtores de `SimuladorTelemetria`, `OrquestradorDespacho` e `navegacao` recebem os valores do `settings.py` sem padrão próprio (hoje o passo até o destino diverge: 300 m × 35 m).
- [ ] **Vindo da Onda 1**: enums em `departamento_origem`/`papel_destinatario`; unificar o nome do campo de atualização (`atualizado_em` × `atualizada_em`, exige migração).

---

## 6. Onda 4 — Frontend

- [ ] **`<TempoRealProvider>`** com uma única conexão WebSocket (hoje até 3 por delegado) e notificações por push no lugar do polling de 15 s.
- [ ] **Componentes comuns**: `<Modal>` (9 cópias do backdrop), `<SeletorOcorrencia>` + `usePaginacao`, `SolicitarLaudoForm` e `ConcederMedidaForm`; manter só um entre `GlideSelect` e `SelectField`.
- [ ] **Quebrar páginas gigantes** em hooks e subcomponentes: `InqueritosPage` (1362), `MedidasProtetivasPage` (998), `TrilhaAuditoriaPage` (875), `ComunicacaoInteragenciasPage` (816), `PainelTaticoPage` (780).
- [ ] **Badges de conexão por `tipo`**, não por `includes('suspeito')` (depende da Onda 2).
- [ ] **Tipos e serviços** centralizados em `types/` (ou `openapi-typescript`); `ocorrenciasService.listar` com objeto de opções.
- [ ] **i18n e estilos**: strings fixas de Interagências, `MapaTatico`, `title`/`placeholder`, `'Sem local'`; estilos inline → classes.
- [ ] **Trilha de auditoria**: incluir no filtro as operações do catálogo que faltam (interagências, inteligência, medida, laudo, inquérito), de preferência vindas da API.
- [ ] **Cypress**: specs para inquéritos, laudos, medidas e interagências.

---

## 7. Onda 5 — Testes e documentação

- [ ] **Traduções faltando** *(encontrado em 08/11)*: 36 das 147 chaves de erro usadas no backend não existem em `infrastructure/i18n/locales/*/default.json` (inquérito 12, laudo 12, medida 11, ocorrência 1); a API devolve a chave crua (ex.: `inquerito.apenas_delegado`) no lugar da mensagem.
- [ ] **Testes unitários que faltam**: inquérito `consultar`/`instaurar`, laudo (4), medida (renovar/revogar), `linha_do_tempo`, `emitir_credencial_telemetria`; concorrência otimista por repositório (estender `tests/integration/contratos/` a inquérito, laudo e medida).
- [ ] **Higiene da suíte**: hash argon2 uma vez por sessão, helper de login único, enum `Papel` nos testes, consolidar fakes duplicadas em `tests/fakes/`.
- [ ] **Wiki** sincronizada com `docs/` (página `Guia-de-Instalacao` inexistente, "11 tabelas", mensageria assíncrona, classificação de extras).
- [ ] **Diagramas**: marcar o diagrama de classes como conceitual ou gerar um novo do código; fontes `.puml` para todos; atualizar o `sq06` com o motor de conexões.
- [ ] **Documentação de engenharia**: diagrama do UC12, UC13 e UC14 documentados, §4.3 e §7 no sumário, `ETAPA-09` e `PLANEJAMENTO_DESENVOLVIMENTO.md` marcados como históricos.
- [ ] **Regras de agentes**: reduzir `.cursorrules` e `.github/copilot-instructions.md` a ponteiros para o `AGENTS.md`.
- [x] **Documentação alinhada ao código**: 23 tabelas, RF10 como extra, UC06 com o Motor de Conexões, UC10 com a regra de sigilo, `AGENTS.md` com os blocos de domínio reutilizáveis. — `2b07f82`, `26da69e`

---

## 8. Trilhas e regras de trabalho

| Trilha | Escopo | Depende de |
| :--- | :--- | :--- |
| C · Aplicação | Onda 2 (base `ComandoAuditado`, mapeadores, motor de conexões) | — |
| D · Persistência | Onda 3: repositório base, mappers, geradores | — |
| E · HTTP e DI | Onda 3: schemas/conversores, `di.py` em providers, import-linter | — |
| F · Frontend | Onda 4 | badges esperam os motivos estruturados da trilha C |
| Todos | Onda 5 e integração na `dev` | — |

- Um PR pequeno por item, saindo da `dev` e voltando para a `dev`, com Conventional Commits.
- Refatoração não muda comportamento: os testes existentes passam sem mudar asserções. Correção de bug entra com teste de regressão.
- Código novo ou refatorado segue o `AGENTS.md` §4 (tipagem completa, docstring com contexto, métodos < 35 linhas, sem números mágicos) e usa os blocos de domínio já existentes.
- Ao concluir um item, marque `[x]` aqui com o hash do commit.
- Antes de cada PR, rode a verificação do `AGENTS.md` §6:

```bash
cd backend && PYTHONPATH=src uv run lint-imports --config pyproject.toml
uv tool run ruff check src tests
uv run pytest --cov
cd ../frontend && npx tsc --noEmit && npm test && npm run build
```
