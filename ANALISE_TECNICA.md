# Análise Técnica — SGOPI Sentinela (out/2026)

> Auditoria estática de todo o repositório (backend, frontend, testes, CI e documentação), feita no branch `dev` (commit `09eaec1`). As referências seguem o formato `arquivo:linha`. Os caminhos de backend são relativos a `backend/src/`, salvo indicação contrária.

## 0. Resumo executivo

**Estado das verificações obrigatórias (AGENTS.md §6)**

| Verificação | Resultado |
|---|---|
| `lint-imports` (contratos hexagonais) | ✅ 3 mantidos, 0 violações |
| `pytest` | ✅ 636 passaram; 13 E2E pulados localmente porque o backend não estava no ar |
| `tsc --noEmit` | ✅ sem erros |

O núcleo do MVP (RF01/RF04/RF02) está bem estruturado:
- máquina de estados com papel exigido nos casos de uso;
- `hash_narrativa` SHA-256 calculado na validação;
- histórico append-only;
- nenhuma deleção física;
- `Relogio` injetado nos casos de uso.

Os problemas graves estão nas **bordas** (HTTP/WebSocket/frontend) e nos **extras** adicionados recentemente (notificações, interagências, medidas, laudos, inteligência).

**Top 10 prioridades**

| # | Severidade | Achado |
|---|---|---|
| 1 | 🔴 Crítica | XSS armazenado: `natureza` é texto livre, aceito sem login no registro público, e vai parar em HTML cru num popup do Leaflet |
| 2 | 🔴 Crítica | O registro público grava as ações como se fossem do usuário real `"agente"`, falsificando a auditoria e a autoria |
| 3 | 🔴 Alta | Qualquer pessoa pode enumerar ocorrências pelo protocolo público sequencial, sem login e sem limite de requisições |
| 4 | 🔴 Alta | O WebSocket envia todos os eventos (incluindo PII de vítimas) a todos os clientes e não reavalia o token depois da conexão |
| 5 | 🔴 Alta | Notificações: qualquer usuário pode marcar a de outro como lida, e o flag `lida` é compartilhado entre todo o papel |
| 6 | 🔴 Alta | O download de laudo nunca acha o arquivo e devolve bytes falsos com o hash verdadeiro no cabeçalho |
| 7 | 🟠 Alta | Corrida entre despacho de apoio e encerramento pode deixar uma viatura presa em `EM_DESLOCAMENTO` |
| 8 | 🟠 Alta | O alerta de medida protetiva permite destinatário arbitrário e monta o HTML do e-mail sem escape |
| 9 | 🟠 Alta | O SMTP usa `starttls()` sem verificar o certificado; a lib JWT `python-jose` não tem manutenção |
| 10 | 🟠 Média | Simulador e orquestrador de despacho automático não têm trava de ambiente e agem sobre dados reais |

---

## 1. Segurança

### 1.1 Críticas / altas

1. **XSS armazenado no Painel Tático.**
   - Onde: `frontend/src/components/painel/MapaTatico.tsx:186-211` monta `popupHtml` com `${a.nome}` e `naturezas_predominantes.join(', ')` e chama `bindPopup(popupHtml)`.
   - Origem do dado: `nome` vem de `calcular_areas_risco.py:122`, que concatena as naturezas. Natureza é `str` livre (`domain/ocorrencia/entity.py:146`) e pode chegar pelo registro público anônimo.
   - O mesmo padrão aparece em `components/painel/leaflet.ts:25,34`.
   - **Correção:** montar o popup com nós DOM (`textContent`) ou escapar o HTML; validar `natureza` contra um catálogo (Enum/tabela).
2. **Registro público se passa por um agente real.**
   - Onde: `adapters/inbound/http/v1/ocorrencias_router.py:138-143` faz `buscar_por_login("agente")` e monta um `Ator(papel=AGENTE)`.
   - Efeitos:
     - a auditoria aponta um policial que não fez nada;
     - esse agente pode corrigir e reenviar o registro;
     - se o usuário não existir, `uuid4()` gera erro de FK e a resposta é 500.
   - **Correção:** criar o papel `CIDADAO` (previsto no RNF02) ou um ator de sistema dedicado, e uma origem `ORIGEM_PUBLICA` na ocorrência. Remover a string mágica `"agente"`.
3. **Enumeração de ocorrências.**
   - `GET /v1/ocorrencias/publico/{protocolo}` (`ocorrencias_router.py:169-182`) não exige login nem limita requisições, e o protocolo é sequencial (`gerador_protocolo_sqlalchemy.py:13`).
   - A resposta expõe `natureza` e `localizacao`.
   - **Correção:** exigir um código secreto entregue no momento do registro (protocolo + token) ou um CAPTCHA, aplicar rate limit e restringir a consulta às ocorrências de origem pública.
4. **WebSocket sem filtro e sem reautenticação.**
   - O token só é validado no handshake (`tempo_real_router.py:79`).
   - Todos os clientes recebem `MEDIDA_VENCIMENTO_ALERTA`, que inclui o e-mail da vítima (`emitir_alerta_vencimento.py:226`), e `NOTIFICACAO_EMITIDA` (`gerir_notificacoes.py:139-153`).
   - Não há checagem de `Origin` nem limite de conexões.
   - **Correção:**
     - criar canais por papel/usuário;
     - tirar PII do payload (o cliente busca o detalhe por REST);
     - fechar o socket quando o token expirar;
     - validar `Origin`.
5. **Notificações.**
   - `MarcarNotificacaoLidaUseCase` (`application/use_cases/notificacao/gerir_notificacoes.py:55-59`) não verifica o destinatário.
   - As notificações por papel e as globais têm um `lida` único (`notificacao_repositorio_sqlalchemy.py:112-134`), então um usuário marca como lida para todos.
   - **Correção:** criar a tabela `notificacoes_leituras (notificacao_id, usuario_id, lida_em)` e checar a posse.
6. **Alerta de vencimento por e-mail.**
   - `emitir_alerta_vencimento.py:147` usa `email_customizado or email_vitima`, e o perfil AGENTE pode escolher qualquer destinatário (`medidas_router.py:221-231`).
   - Os nomes da vítima e do agressor entram no HTML sem escape (`:159,:165`).
   - O modo manual ignora a deduplicação de 48h.
   - **Correção:** escapar o HTML, restringir o destinatário a contatos cadastrados, aplicar rate limit e auditar o destinatário.
7. **SMTP sem verificação de certificado.**
   - `enviador_email_smtp.py:187` chama `starttls()` sem `ssl.create_default_context()`.
   - Com `smtp_usar_tls=False`, a senha trafega em claro.
8. **Validação fraca de segredos em produção** (`infrastructure/settings.py:98-101`):
   - o placeholder do `.env.example` tem mais de 32 caracteres e passa na checagem;
   - um segredo vazio cai no default de dev;
   - não há checagem da senha padrão do banco, do CORS `*` nem das flags de simulador/orquestrador.
9. **Autenticação.**
   - Um token continua válido por até 8h depois que o usuário é desativado: `deps.py:131-136` não checa `ativo`.
   - `python-jose` não tem manutenção e possui CVEs; migrar para `PyJWT`.
   - É possível descobrir logins existentes pelo tempo de resposta, pois não há hash fictício quando o login não existe (`autenticar_usuario.py:94-95`).
   - O rate limit usa a chave `login|ip`, o que permite password spraying.
   - O limitador fica em memória, cresce sem limite e não funciona com várias instâncias (`limitador_em_memoria.py:42`).
   - Não existe política de senha.
10. **Demonstração em produção.**
    - O seed usa a mesma senha `Senha@123` para todos os usuários e não tem trava de ambiente (`backend/scripts/seed.py:24`). Essa senha também aparece no bundle do frontend (`locales/*/auth.json:16`, `dica_seed`).
    - `/v1/simulador/ligar` não tem guarda de `app_env` (`viaturas_router.py:104-114`).
    - O orquestrador despacha e encerra **qualquer** ocorrência `VALIDADA` com um desfecho fictício (`orquestrador_despacho.py:222-251`).
    - Qualquer papel lista todos os logins (`usuarios_router.py:14`).
    - `/docs` e `/openapi.json` ficam públicos em produção (`main.py:234`).

### 1.2 Médias / baixas
- O `X-Request-ID` do cliente entra nos logs sem validação (`middleware.py:210`), e o middleware usa um hack com `locals()` (`:219`).
- O CORS tem `allow_credentials` com métodos e headers `*` (`main.py:242-249`), o que é desnecessário com Bearer.
- Interagências: qualquer papel lê qualquer `nivel_sigilo` (`interagencias_router.py:141-145`).
- O endpoint público `/v1/publico/documentos` busca por `hash_narrativa`, que não tem índice, e não tem rate limit.
- `EnviadorEmailSMTP.emails_enviados` cresce sem limite e mantém PII em memória; e-mails de destinatários vão para o log (`enviador_email_smtp.py:148-166`).
- O `docker-compose.yml` usa a senha `admin` e publica a porta 5432 em todas as interfaces.

---

## 2. Bugs de correção

### 2.1 Backend
| Severidade | Local | Problema | Correção sugerida |
|---|---|---|---|
| Alta | `adapters/inbound/http/v1/laudos_router.py:195-208` | O arquivo é salvo com chave UUID (`anexar_laudo.py:65`), mas o download lê `f"{hash}.pdf"`. Sempre devolve `b"%PDF-1.4 demo laudo"`; o import de `infrastructure.di` dentro da rota fica sem uso | Persistir `chave_arquivo` no laudo e mover a leitura para um caso de uso `BaixarLaudo` com auditoria; limitar o tamanho do upload (`:165`) |
| Alta | `application/use_cases/despacho/despachar_viatura.py:102-114` | No despacho de apoio a ocorrência não é salva, então `versao` não é checada. Em concorrência com `EncerrarOcorrencia`, uma ordem ativa fica numa ocorrência `ENCERRADA` e a viatura fica presa | Sempre incrementar a versão da ocorrência; adicionar um índice único parcial "1 ordem ativa por viatura" |
| Alta | `adapters/inbound/websocket/gerenciador_conexoes.py:44-45` | Recria `list(self._conexoes)` antes e depois de um `await`; o `zip` desalinha e descarta o socket errado | Tirar um snapshot único; `asyncio.wait_for` por envio; publicar fora da requisição (fila/`create_task`) |
| Média | `domain/ocorrencia/entity.py:455-467` | Arquivar ou excluir uma ocorrência vinculada a inquérito mantém `inquerito_id` sem nenhuma guarda | Bloquear a ação ou exigir desvínculo antes |
| Média | `domain/medida_protetiva/entity.py:56`, `domain/notificacao/entity.py:53,90`, `domain/interagencias/entity.py:69,114` | `datetime.now()` naive no domínio, misturado com o `Relogio` aware, pode gerar `TypeError` | Receber `agora` como parâmetro |
| Média | `emitir_alerta_vencimento.py:61` | Usa `agora.date()` em UTC, então o vencimento sai errado entre 21h e 24h no horário de Brasília | Converter para `America/Sao_Paulo` antes de pegar `.date()` |
| Média | `registrar_posicao_viatura.py:66` + `infrastructure/di.py:505` | A tolerância de timestamp é usada como idade máxima do sinal (só coincidem por acaso, 60s); o caso de uso não recebe `Ator` | Separar os dois parâmetros; exigir papel |
| Média | `anexar_evidencia.py:91,119` | O arquivo é salvo antes do `commit`, então uma falha deixa o arquivo órfão | Salvar depois do commit ou compensar |
| Média | `corrigir_ocorrencia.py:62-80` | A auditoria só registra a descrição; mudanças em natureza, envolvidos, coordenada e data/hora do fato não ficam registradas (RNF03) | Gerar diff completo antes/depois |
| Média | `entity.py:384,391` | `validada_por_id` é preenchido também ao devolver e ao rejeitar | Criar o campo `revisada_por_id` |
| Média | `comunicacao_interagencias_repositorio_sqlalchemy.py:104-110` | O filtro por departamento roda em Python depois do `LIMIT 50` | Filtrar no SQL |
| Média | `notificacoes_router.py:88-98` | `offset` é ignorado e `total=len(itens)` | Paginar no repositório |
| Média | `calcular_areas_risco.py:54` | O heatmap conta ocorrências `EXCLUIDA`/`REJEITADA` | Filtrar por status válidos |
| Média | `consultar_inqueritos.py:73,116,182` | N+1 em `buscar_por_id` | Busca em lote |
| Média | `ocorrencia_repositorio_sqlalchemy.py:49-55` | A listagem carrega cinco coleções filhas, incluindo PII | Criar uma projeção leve para listas |
| Baixa | Migração `0011` | Os nomes de índice divergem do modelo, e os guards "if not exists" escondem a divergência | Gerar uma migração de correção; checar divergência no CI |
| Baixa | Migração `0001` | O downgrade apaga `registros_auditoria` | Bloquear o downgrade da auditoria |
| Baixa | `emitir_alerta_vencimento.py:185-245` | E-mail e evento saem antes do commit, e o lote de até 500 roda dentro da requisição HTTP sem agendador | Usar outbox + job agendado |

### 2.2 Frontend
| Severidade | Local | Problema |
|---|---|---|
| Alta | `pages/PainelTaticoPage.tsx:82-83` | A opção `'OPERADOR'` não existe (o papel é `OPERADOR_CENTRAL`), então os alertas não chegam a ninguém; o rótulo "Supervisores e Delegados" só cobre SUPERVISOR |
| Alta | `pages/ComunicacaoInteragenciasPage.tsx:32` + `i18n.ts` | O namespace `interagencias` não está registrado e não há JSON em `locales/`, então a interface em inglês aparece em português |
| Média | Vários (`PainelTaticoPage`, `MedidasProtetivasPage`, `NotificationBell`, `Sidebar:195`) | Cerca de 40 chaves i18n não existem em nenhum locale e só funcionam pelo fallback inline |
| Média | `components/painel/MapaTatico.tsx:65-74` | O cleanup não limpa `viaturasRef`/`ocorrenciasRef`/`rotasRef`; com StrictMode, os marcadores ficam ligados ao mapa antigo |
| Média | `services/tempoRealService.ts:54,77` | Código 1008 encerra sem disparar `sgopi:sessao-expirada`; sem token desiste para sempre e o hook (deps `[]`) não reconecta depois do login |
| Média | `components/RequireRole.tsx:11` | Não reavalia `expira_em`, então a UI continua "logada" depois das 8h |
| Média | Páginas com fetch (`PainelTatico`, `FilaDelegado`, `Frota`, `Inicio`, `Laudos`…) | Sem `AbortController`, uma resposta antiga pode sobrescrever a nova; faltam estados de carregamento |
| Média | `pages/AutenticarDocumentoPage.tsx:78-79` | Requisição duplicada (navigate + chamada direta) |
| Média | `components/painel/SeletorCoordenada.tsx:131,143` | Campo vazio vira `Number('') = 0`, então a coordenada vai para 0 |
| Baixa | `RegistroCidadaoPage:167`, `TrilhaAuditoriaPage:161`, `hooks/useToast.tsx:14` | `setTimeout` sem cleanup |

---

## 3. Lacunas frente à documentação (`DOCUMENTACAO_DE_ENGENHARIA.md`)
- **UC04, Exceção I:** uma tentativa negada deve ser auditada. `Ator.exigir_papel` (`application/.../ator.py:18`) só lança a exceção; só a dependência HTTP (`deps.py:69`) audita. O caminho via WebSocket, simulador e orquestrador não audita.
- **UC04, passo 2:** a fila deve ser ordenada por "antiguidade **e gravidade**". Não existe o atributo gravidade.
- **UC04, passo 9:** "Notificar o Agente autor". Validar, devolver e rejeitar não criam `Notificacao`.
- **UC02, Exceção I:** não é possível informar manualmente uma posição recebida "via rádio".
- **UC02, Exceção II:** a "fila de prioridade máxima" não está implementada.
- **§5.7.2:** não há cancelamento de ordem nem recolhimento de uma viatura específica; só o encerramento da ocorrência libera viaturas.
- **RNF02:** o papel Cidadão não existe em `Papel` (`domain/usuario/entity.py:16`).
- **Diagramas:** só `sq04` tem fonte `.puml`; os outros são apenas PNG e não podem ser mantidos nem comparados em diff.

---

## 4. Violações das diretrizes do AGENTS.md
- **Métodos com mais de 35 linhas.**
  - No núcleo:
    - `registrar_ocorrencia_policial.py:46` (60)
    - `corrigir_ocorrencia.py:30` (54)
    - `Ocorrencia.registrar` (48)
    - `_mapeadores.para_detalhe` (45)
    - `anexar_evidencia.py:84` (44)
    - `Ocorrencia.corrigir` (43)
  - Nos extras:
    - `emitir_alerta_vencimento.py:121` (**145**)
    - `gerir_comunicacoes.py:52` (97)
    - `vincular_ocorrencias.py:37` (92)
    - `instaurar_inquerito.py:41` (86)
    - `buscar_conexoes.py:21` (86)
    - `calcular_areas_risco.py:49` (85)
- **Strings mágicas.**
  - Operações da máquina de estados (`status.py:29-34`).
  - Status duplicados em `domain/ocorrencia/eventos.py:17-45`.
  - Literais `operacao`/`entidade` de auditoria em todos os casos de uso.
  - `Viatura.sinal` retorna `"OK"`/`"SEM_SINAL"`.
  - Os estados de integridade de evidência incluem `ARQUIVO_AUSENTE`, que não está no `Literal`.
- **Nome do método principal:** o AGENTS.md pede `execute()` e o código usa `executar()` de forma consistente. Sugestão: **atualizar o AGENTS.md** em vez do código.
- **Tipagem ausente** em `revisar_ocorrencia.py:93-126`, `arquivar_ocorrencia.py` e `registrar_posicao_viatura.py:68`.
- **Código morto:** `ESTADOS_TERMINAIS` (`status.py:37`) e `desvincular_inquerito`.
- **Duplicação:**
  - a construção de `Envolvido` está repetida em registrar e corrigir, e o privado `_tipo_envolvido` é importado entre módulos;
  - `PAPEIS_CONSULTA` é definido duas vezes com membros diferentes;
  - helpers compartilhados (`carregar_ou_404`, `para_output`) estão em módulos de consulta.
- **Contrato de camadas:** a ordem `adapters > infrastructure` permite que adapters importem infrastructure, e o próprio `laudos_router.py:196` faz isso. Avaliar um contrato que proíba explicitamente `adapters -> infrastructure.di`.

---

## 5. Testes
- **Frontend sem testes unitários:** não há vitest/jest. Utilitários puros (`utils/manchas.ts`, `cpf.ts`, `autenticidade.ts`, `datas.ts`) e o backoff de `ClienteTempoReal` estão sem cobertura.
- **Cypress (35 testes):**
  - não cobre inquéritos, laudos, medidas, interagências, frota, `/consulta`, `/registrar-cidadao`, notificações nem troca de idioma;
  - o seed não cria PERITO nem SUPERVISOR;
  - `cy.wait(3000)` em `validacao-despacho.cy.ts:20`.
- **Backend sem testes unitários** nos casos de uso de `inquerito/*`, `laudo/*` e `medida_protetiva/{conceder,consultar,renovar,revogar}`. Os testes HTTP desses módulos têm só 1 ou 2 casos cada.
- **Rotas sem teste:** `POST /v1/inqueritos/{id}/ocorrencias` e `GET /v1/laudos/{id}/download`; este último teria revelado o bug 2.1.
- **Repositórios:** só o de ocorrência tem teste de persistência direto.
- **Fakes:** `tests/fakes/` não tem fakes das portas novas, e cada teste redefine os seus, o que contradiz o README:267.
- **Testes instáveis:** `asyncio.sleep(0.05/0.12)` em `test_viaturas*.py` e `datetime.now()` em testes de domínio.
- **CI só usa SQLite:** os triggers append-only do Postgres e os `ON CONFLICT` dos contadores de protocolo nunca são testados.

---

## 6. CI, infraestrutura e documentação
- **CI** (`.github/workflows/ci.yml`):
  - falta ruff/mypy/bandit/pip-audit/`npm audit`;
  - não há service Postgres;
  - não há checagem de divergência do Alembic (`alembic check`);
  - `npm ci || npm install` esconde divergência do lockfile;
  - o Cypress não roda;
  - o E2E sobe com o segredo JWT padrão.
- **Não há Dockerfile** de backend nem de frontend; o compose só tem o banco. O diretório de evidências é um caminho relativo ao cwd (`settings.py:69`).
- **`/health`** só roda `SELECT 1`: não separa liveness de readiness, não checa se as migrações estão em head nem o estado das tarefas de fundo.
- **Paginação ausente** em `/v1/usuarios`, `/v1/viaturas` e `/v1/interagencias`; `/v1/auditoria` e `/v1/despachos` só têm `limit`.
- **Arquivos soltos na raiz:** `pyproject.toml` e `uv.lock` na raiz são stubs (`requires-python >=3.14`, sem dependências) que conflitam com `backend/` (>=3.13). Remover.
- **Scripts de issues:** `scripts/cadastrar_issues_*.py` são três scripts sobrepostos (cerca de 1.350 linhas), com `REPO` fixo, e `--token` por CLI vai para o histórico do shell. Consolidar ou remover.
- **Seed:** `backend/scripts/seed.py:86-90` engole a falha de `seed_ocorrencias` com `print`.
- **README desatualizado:**
  - :113 diz que `/consulta` é "tempo real", mas a página faz um fetch único;
  - :132 cita 613 testes, mas hoje são 649 coletados;
  - :98 sugere SQLite sem Docker, mas `aiosqlite` só existe no grupo dev;
  - :267 diz que há fakes de todas as portas.
- `docs/implementacao/ETAPA-09-testes-e2e.md:27-29` diz que o E2E roda com SQLite, enquanto o README usa Postgres.
- **Aviso de depreciação:** `starlette.testclient` com `httpx`.

---

## 7. Sugestões de novas funcionalidades
Separadas entre as que **reforçam o MVP** (RF01/RF04/RF02, alinhadas ao escopo canônico) e as que dependem de **aprovação da equipe** (expandem extras), conforme AGENTS.md §1.3.

### 7.1 Dentro do escopo do MVP (recomendadas)
1. **Gravidade e prioridade da ocorrência** (UC04 passo 2, UC02 Exc. II): Enum `Gravidade` derivado de um catálogo de naturezas, fila do delegado ordenada por gravidade e antiguidade, e despacho com prioridade máxima.
2. **Catálogo de naturezas** (tabela/Enum): resolve o XSS na origem, padroniza o heatmap e permite estatísticas.
3. **Cancelar ordem de despacho / recolher viatura** (§5.7.2), com motivo obrigatório e auditoria.
4. **Posição manual "via rádio"** (UC02 Exc. I), marcada como fonte `MANUAL` na telemetria.
5. **Notificação ao agente autor** em validar, devolver e rejeitar (UC04 passo 9), reaproveitando o módulo de notificações já existente.
6. **Painel de SLA:** tempo entre registro e validação e entre despacho e chegada no local (dados já existentes em `historico_status_ocorrencia`).
7. **Verificação de integridade da auditoria:** encadear hashes dos `registros_auditoria` (hash do registro anterior) e oferecer um endpoint para verificar a cadeia, reforçando o RNF03.
8. **Sugestão de viatura por ETA real** (rota OSRM) em vez de distância em linha reta.

### 7.2 Extras (exigem aprovação)
- Papel `CIDADAO` com conta leve ou código de acompanhamento, e atualização da consulta pública por SSE/WS (como o README promete).
- Agendador (APScheduler ou cron) para alertas de vencimento de medidas, com outbox de e-mails.
- Exportação de relatórios (PDF/CSV) das ocorrências e da trilha de auditoria.
- Modo offline / PWA para o agente em campo, com fila de envio.
- MFA (TOTP) para Delegado e Supervisor.
- Observabilidade: métricas Prometheus e tracing OpenTelemetry.

---

## 8. Roteiro sugerido
| Fase | Itens |
|---|---|
| **Sprint 1: segurança urgente** | 1.1 itens 1 a 6, 8 e 10; bug do download de laudo; opção `OPERADOR` |
| **Sprint 2: integridade** | Corrida do despacho de apoio + índice "1 ordem ativa por viatura"; datetimes naive; broadcast WS; auditoria completa de `corrigir`; migração `PyJWT` e SMTP TLS |
| **Sprint 3: qualidade** | Service Postgres + `alembic check` + ruff/mypy/pip-audit no CI; Vitest no frontend; testes dos casos de uso de inquérito, laudo e medida; fakes compartilhados; refatoração dos métodos com mais de 35 linhas |
| **Sprint 4: MVP+** | Gravidade/prioridade, catálogo de naturezas, cancelamento de ordem, notificação ao agente autor, posição manual |
| **Contínuo** | i18n completo, acessibilidade (modais com `role="dialog"`, itens clicáveis com teclado), quebrar páginas com mais de 400 linhas, Dockerfiles, atualizar o README |
