# Correções da Análise Técnica (revisão 2) — SGOPI Sentinela

> Executadas em 05/10/2026 no branch `matheus-Fastapi`, a partir de [`ANALISE_TECNICA_2026-10-05.md`](ANALISE_TECNICA_2026-10-05.md).
> A ordem seguida foi a de severidade: **críticos → altos → médios → baixos**. Nada foi commitado: as mudanças estão no working tree para revisão.
>
> Caminhos de backend são relativos a `backend/src/`, salvo indicação contrária.

---

## 0. Resumo

| Verificação | Antes | Depois |
|---|---|---|
| `lint-imports` | 3 contratos, 0 violações | **4 contratos**, 0 violações (novo contrato: adapters de entrada não tocam banco/ORM) |
| `pytest --cov` | 636 ok + 13 pulados, 93 %, **1 teste intermitente** | **744 ok** (731 + 13 E2E de API rodando contra o backend no ar), **95,6 %**, sem avisos |
| Piso de cobertura por arquivo | inexistente (`vincular_ocorrencias` 22 %, `buscar_conexoes` 43 %) | todos os arquivos acima do piso (85 % `domain/`, 75 % `application/`) |
| `alembic check` (SQLite e PostgreSQL 16) | ❌ 4 operações pendentes (+3 UNIQUE redundantes no Postgres) | ✅ sem divergência; `upgrade → downgrade 0011 → upgrade` validado nos dois bancos |
| `ruff check src tests` | 487 apontamentos | ✅ 0 (com configuração no `pyproject.toml`) |
| `tsc --noEmit` | ✅ | ✅ |
| `npm run build` | bundle único de 941 kB (aviso de chunk) | maior chunk 259 kB, **sem aviso**; CSP injetado no `index.html` de produção |
| `npm audit --omit=dev` | 2 moderadas (`react-router`) | **0 vulnerabilidades** |
| Vitest (frontend) | inexistente | 7 testes |
| Cypress | 35 testes | 36 testes (novo spec de regressão do XSS); todos verdes — ver ressalva em §5 |

**Top 10 da análise:** todos os 10 itens foram tratados. Dos 13 achados novos (N1–N13), 13 foram tratados (N8 pela remoção do caminho morto — ver §3).

---

## 1. Críticos

### #1 — XSS armazenado no popup/tooltip do Leaflet
**O que foi feito**
- Novo utilitário `frontend/src/utils/html.ts` → `escaparHtml()`.
- Aplicado em **todos** os pontos em que o Leaflet recebe string como HTML: o popup das áreas de risco, os três `bindTooltip` do `MapaTatico.tsx` (o tooltip do marcador de ocorrência também era vulnerável, pois mostra `natureza`) e os `divIcon` de `components/painel/leaflet.ts` (prefixo, protocolo e rótulos dos pins).
- **Defesa em profundidade:** plugin no `vite.config.ts` injeta uma *Content-Security-Policy* só no build de produção (`script-src 'self'`, `object-src 'none'`, `img-src` com os tiles OSM e `connect-src` incluindo a origem de `VITE_API_BASE_URL`, quando configurada). Em `vite dev` não entra, porque o preâmbulo do React Refresh é um script inline.

**Como foi validado**
- `frontend/cypress/e2e/xss-painel.cy.ts`: registra uma ocorrência com `natureza = <img src=x onerror=...>`, valida e abre o Painel; o tooltip mostra o texto literal e o `onerror` não executa. Fiz o teste de mutação: removendo o escape, o spec **falha**; com o escape, passa.
- Vitest em `src/utils/__tests__/html.test.ts`.

> `natureza` continua texto livre: a opção "Outro" do registro público aceita natureza personalizada por desenho. Restringir a um catálogo é decisão de produto e ficou de fora.

### #2 — Registro público gravado como o usuário real `agente`
**O que foi feito**
- `Papel.CIDADAO` e `Usuario.sistema_cidadao()` (`domain/usuario/entity.py`): usuário de sistema **inativo** e com hash de senha inutilizável, então nunca autentica.
- Migração **`0013`** cria o usuário `sistema.cidadao` e as colunas `ocorrencias.origem` e `ocorrencias.codigo_acompanhamento_hash`.
- `OrigemOcorrencia` (`POLICIAL | PUBLICA`) no agregado `Ocorrencia`, persistida pelo repositório e exposta no resumo/detalhe.
- `RegistrarOcorrenciaPublica` monta o ator de sistema internamente. Se a base não tiver o usuário (por exemplo, nos testes), ele é criado. O router deixou de fazer `buscar_por_login("agente")` e acabou o `uuid4()` que gerava erro de FK (500).
- `RegistrarOcorrenciaPolicial` exige o papel conforme a origem: `AGENTE` para policial e `CIDADAO` para pública. Um agente não consegue registrar como canal público, e vice-versa.
- **Regra de domínio nova:** comunicação pública **não pode ser devolvida para correção**, pois não há agente autor para corrigi-la e ela ficaria presa em `EM_CORRECAO`. O Delegado valida, rejeita ou arquiva. A Fila do Delegado esconde o botão "Devolver" e mostra o aviso (i18n pt/en).
- A auditoria de `ocorrencia.registrar` passa a registrar a `origem`.

### #6 — Enumeração de ocorrências pelo protocolo sequencial
*(Tratado junto com o #2, porque depende da origem pública.)*
- **Código de acompanhamento** com 10 caracteres digitáveis (≈ 50 bits), entregue uma única vez no recibo. Só o SHA-256 dele é persistido, e a comparação é em tempo constante (`domain/ocorrencia/comunicacao_publica.py`).
- A consulta virou `POST /v1/ocorrencias/publico/consulta` com `{protocolo, codigo_acompanhamento}`. O corpo vai no POST para não deixar o código nos logs de URL.
  - Só alcança ocorrências de **origem pública**.
  - Qualquer falha devolve o mesmo 404: protocolo inexistente, código errado, origem policial ou ocorrência excluída. A rota não serve de oráculo.
- **Rate limit por IP** com limitador próprio (`CONSULTA_PUBLICA_*` no `.env`), aplicado também em `GET /v1/publico/documentos/{codigo}`, que antes não tinha limite.
- Frontend:
  - o recibo exibe o código;
  - a página `/consulta` pede protocolo + código;
  - o botão "Acompanhar" passa o código via *state* do router, nunca pela URL.

---

## 2. Altos

### #3 — WebSocket: broadcast com PII e token validado só no handshake
- `adapters/inbound/websocket/audiencia.py`: a regra de audiência é definida **por tipo de evento**.
  - Eventos operacionais (ocorrência, viatura, despacho) seguem para qualquer sessão autenticada.
  - Notificação pessoal vai só ao destinatário; notificação por papel, só ao papel.
  - Alertas de medida e de interagências seguem os mesmos papéis das rotas REST.
  - Tipo desconhecido não é entregue (**falha fechada**).
- `GerenciadorConexoes` guarda a `Sessao` (ator + expiração do token). Sessões vencidas são fechadas com **1008**, tanto na transmissão quanto a cada keep-alive do cliente.
- O handshake confere:
  - o **`Origin`** contra a lista do CORS, contra Cross-Site WebSocket Hijacking;
  - se o **usuário segue ativo**.
- O `zip` desalinhado foi corrigido: um snapshot único, `strict=True` e timeout de 5 s por envio. Há teste de regressão com o socket falho no meio da lista.
- PII removida: `MEDIDA_VENCIMENTO_ALERTA` não carrega mais o e-mail do destinatário.
- Frontend: código 1008 dispara `sgopi:sessao-expirada`, como o 401 do REST.

### #4 — Notificações: `lida` compartilhado e sem checagem de posse
- Tabela nova `notificacoes_leituras (notificacao_id, usuario_id, lida_em)`, criada pela migração **`0014`**. A leitura passa a ser **por usuário**.
- O backfill migra as leituras de notificações **pessoais**; as de papel/difusão não têm autor identificável e voltam a ficar pendentes.
- `Notificacao.destinada_a()` no domínio. `MarcarNotificacaoLida` devolve 404 para quem não é destinatário, sem revelar se a notificação existe.
- A listagem agora respeita `offset`, que antes era ignorado.

### #5 — Download de laudo com chave errada e bytes falsos
- Novo caso de uso `BaixarArquivoLaudo` (`application/use_cases/laudo/baixar_laudo.py`):
  - lê pela `arquivo_chave` gravada na anexação;
  - **confere o SHA-256** antes de entregar: 409 se adulterado, 404 se o arquivo sumiu;
  - **audita** cada download (`laudo.download`).
- O router perdeu o import de `infrastructure.di` dentro da rota e o fallback `b"%PDF-1.4 demo laudo"`.
- O upload de laudo ganhou limite de tamanho (o mesmo das evidências).

### #7 — Corrida entre despacho de apoio e encerramento
- `Ocorrencia.registrar_apoio()` incrementa a versão sem mudar o status, e o despacho **sempre** salva a ocorrência. Um encerramento concorrente passa a ser detectado pelo optimistic locking (409).
- Migração **`0015`**: índice único parcial `uq_ordens_despacho_viatura_ativa (viatura_id) WHERE ativa`. Ele verifica antes se a base já tem duplicidades e falha com mensagem clara, se houver. O repositório traduz o `IntegrityError` em 409.
- Teste que simula o encerramento entre a leitura e a gravação do apoio.

### Altos herdados da análise anterior (ainda abertos e tratados)
- **SMTP sem verificação de certificado:**
  - `starttls(context=ssl.create_default_context())`;
  - credenciais nunca são enviadas sem TLS;
  - o destinatário aparece mascarado nos logs (`c***@dominio`);
  - o histórico em memória é limitado a 100 itens.
- **Token válido após desativar o usuário:** `ator_atual` (HTTP) e o handshake do WebSocket consultam `ativo` a cada requisição. No WS, a conexão do pool é liberada logo após a checagem.
- **E-mail do alerta de medida protetiva:**
  - todo texto do cadastro passa por `html.escape`;
  - o destinatário "customizado" precisa ser um e-mail **cadastrado** para algum envolvido da ocorrência, para o sistema não servir de relay com timbre oficial;
  - o método de 145 linhas foi quebrado em funções curtas.

---

## 3. Médios

| Item | O que foi feito |
|---|---|
| **N1** teste intermitente | `test_publico_http.py` agora procura o documento completo (`123.456.789-09` / `12345678909`) e não o trecho `"789"`, que aparecia por acaso no hash. A falha intermitente desta sessão foi reproduzida e era exatamente esse teste; depois da correção, a suíte passou 5 vezes seguidas. |
| **N2** divergência de migrações | Migração **`0012`**: renomeia os índices de `comunicacoes_interagencias` e remove 4 constraints UNIQUE redundantes no Postgres (`0008`/`0011`), já cobertas pelo índice único do modelo. CI: `alembic check` no job SQLite e **job novo com PostgreSQL 16** (upgrade → check → downgrade 0011 → upgrade → seed). |
| **N3** alerta tático sem validação | `AlertaCriticidadeRequest` usa `NivelCriticidadeAlerta` (Enum novo) e `Papel` (recusa `CIDADAO`), e as coordenadas e o raio ganharam limites. Valor inválido vira 422 em vez de alerta que não chega a ninguém. Frontend: as opções saem de `Papel` (`PAPEIS_DESTINATARIOS_ALERTA`), o que acaba com o `'OPERADOR'` inexistente. Os rótulos foram para o i18n (`painel.alerta.*`, pt/en), e o bloco `alerta` foi criado, porque o namespace não tinha nenhuma dessas chaves. |
| **N4** revalidação de integridade a cada abertura | O detalhe **não verifica mais automaticamente**: o estado inicial é "não verificada" e há o botão "Verificar integridade". O download continua conferindo o SHA-256 no servidor. `EstadoIntegridadeEvidencia` virou Enum de domínio com `ARQUIVO_AUSENTE`, e `verificado_em` virou `datetime` no DTO (serializado na borda). |
| **N5** `hash_narrativa` ambíguo | **Hash v2** em JSON canônico (`sort_keys`, separadores fixos, campos nomeados), incluindo o SHA-256 das **evidências**, que não mudam após a validação. Os itens apreendidos ficaram de fora, porque a custódia continua mudando depois da emissão. Migração **`0016`** cria `hash_versao` e marca os documentos já emitidos como v1, que **continuam verificáveis**. Há teste mostrando a colisão na v1 e a ausência dela na v2. |
| **N6** bundle sem divisão | `React.lazy` por rota (exceto a Landing) + `manualChunks` (`leaflet`, `react`, `i18n`) + `Suspense` dentro do router. O cidadão em `/registrar-cidadao`/`/autenticar` não baixa mais Leaflet nem as páginas internas. |
| **N8** geocodificação direta ao Nominatim | Na verificação, `LocalOcorrencia.tsx` e `geocodificacaoService.ts` **não eram importados por nenhuma tela**: o formulário usa `SeletorCoordenada` desde o commit `440de29`. O vazamento existia só como caminho latente. Os dois arquivos foram removidos e o Nominatim saiu do CSP. |
| **N10** buracos de cobertura | `vincular_ocorrencias` e `buscar_conexoes` foram refatorados (métodos < 35 linhas, pesos da pontuação como constantes) e ganharam 9 testes. Entraram testes de domínio para `inquerito` e `interagencias`. Script `backend/scripts/verificar_cobertura_por_arquivo.py`, com passo no CI. |
| **N11** travas de demonstração em produção | `Settings._validar_seguranca` agora **recusa subir** em produção com: segredo JWT curto ou de exemplo, senha padrão do banco, CORS `*`/local, SMTP sem TLS, despacho automático ou gerador ligados. O endpoint `/v1/simulador/ligar` devolve 403 em produção. |
| **N12** telemetria sem identidade de dispositivo | Porta `CredencialDispositivo` + adapter HMAC-SHA256 por viatura (`TELEMETRIA_SEGREDO_DISPOSITIVOS`). Caso de uso **auditado** `EmitirCredencialTelemetria` (`POST /v1/viaturas/{id}/credencial-telemetria`). O rastreador envia `X-Credencial-Dispositivo`, que só vale para a própria viatura. **Em produção, token humano é recusado** (403). A auditoria da chegada ao local registra autor e origem. |
| **N13** `python-jose` | Migrado para **PyJWT** (`ProvedorTokenJWT`). `python-jose`, `ecdsa` e `rsa` saíram do `uv.lock`. Os tokens são compatíveis (mesmas claims). O import-linter proíbe `jwt` em `domain`/`application`. O segredo de desenvolvimento passou a ter ≥ 32 bytes (RFC 7518). |
| Datetimes naive no domínio | Defaults *aware* (UTC). `instante` passou a ser **obrigatório** em `Notificacao.criar` e `ComunicacaoInteragencias.criar`. Novo `domain/shared/tempo.py`: o vencimento de medida é contado no fuso `America/Sao_Paulo`, o que corrige o erro de um dia entre 21h e 24h. |
| CORS / `/docs` / `X-Request-ID` | `allow_credentials=False` (a autenticação é Bearer) e métodos/headers explícitos. `/docs`, `/redoc` e `/openapi.json` ficam desligados em produção. `X-Request-ID` só é aceito se casar com `^[A-Za-z0-9._-]{1,64}$` (evita log injection), e o hack com `locals()` foi removido. |
| i18n `interagencias` ausente | Namespace criado (`locales/{pt,en}/interagencias.json`) e registrado no `i18n.ts`. |

---

## 4. Baixos

| Item | O que foi feito |
|---|---|
| **N7** `react-router-dom` com advisories | Atualizado para **7.18** (não há correção na linha 6.x). `tsc`, build e Cypress verdes; `npm audit` com 0 vulnerabilidades. `npm audit --omit=dev --audit-level=high` entrou no CI. |
| **N9** higiene `ruff` | Configuração em `backend/pyproject.toml`: B008 tratado via `extend-immutable-calls` para o idioma FastAPI; UP042 ignorado de propósito, ver §6. 105 correções automáticas + 10 manuais. Passo no CI. O `ocorrencias_router.py` (563 linhas, imports `E402`) foi dividido em `ocorrencias_router`, `ocorrencias_publico_router`, `evidencias_router` e `revisao_router`. As 18 rotas de `/v1/ocorrencias` foram conferidas no OpenAPI. |
| Contrato de camadas (§3.1.3) | Novo contrato no import-linter: `adapters.inbound` não importa `infrastructure.database`, `sqlalchemy` nem `adapters.outbound.persistence`. |
| Vitest (§3.2) | Instalado, com testes de `escaparHtml`, CPF e chave de autenticidade. `npm test` entrou no CI. |
| `window.confirm` (§3.4) | Novo `components/common/ConfirmDialog.tsx`: `role="alertdialog"`, foco inicial em "Cancelar", Esc e clique fora cancelam. Usado na Fila do Delegado (rejeitar, arquivar e excluir). O spec Cypress foi ajustado. |
| Aviso `starlette.testclient` | Resolvido com `httpx2` (dev). O filtro amplo foi trocado por um filtro só do aviso de terceiros (alias do anyio usado pela starlette 1.6). A suíte roda **sem avisos**. |
| `pyproject.toml`/`uv.lock` órfãos na raiz | Removidos (sem dependências e com `requires-python >=3.14`; o projeto real está em `backend/`). |
| README | Tabela de qualidade atualizada e comandos novos documentados (`ruff`, `alembic check`, piso por arquivo, Vitest e `npm audit`). |

### Achados extras durante a validação
- **Bug pré-existente no detalhe da ocorrência** (introduzido em `969a0b4`): o `useEffect` que volta para a aba "Detalhe" dependia de `o.envolvidos`. Por isso, **todo recarregamento** do detalhe (por exemplo, ao registrar uma apreensão) tirava o usuário da aba de Apreensões. Agora a aba e o comprovante só são reiniciados quando muda a ocorrência.
- **Specs Cypress desatualizados** (`registro.cy.ts`, `apreensoes.cy.ts`): eles clicavam no `<summary>` "Informar coordenadas manualmente" do componente morto citado no N8. Foram ajustados para a UI atual.

---

## 5. Como foi validado

1. A cada item: testes unitários e de integração novos ou ajustados, mais a suíte completa.
2. Migrações:
   - `upgrade head`, `alembic check` e `downgrade 0011 → upgrade head` em **SQLite limpo** e em um **Postgres descartável** (`sgopi_check`, no container `sgopi_db`), seguidos do seed.
   - **O banco `sgopi` de desenvolvimento não foi alterado**: continua na revisão `0011`.
3. Ponta a ponta:
   - backend (`uvicorn`) apontando para `sgopi_check` e frontend em `vite dev`;
   - os **13 E2E de API do pytest** rodando contra o servidor;
   - Cypress:
     - a suíte completa rodou com 29/35;
     - as 6 falhas eram os dois problemas pré-existentes da seção "Achados extras";
     - depois das correções, `registro` + `apreensoes` (13/13) e o novo `xss-painel` passaram isoladamente;
     - **ressalva:** a última passada da suíte completa, depois da correção da aba do detalhe, não pôde ser executada por indisponibilidade da ferramenta. Vale rodar `npx cypress run` mais uma vez;
   - smoke test do canal público por `curl`: registro com código → consulta OK, código errado → 404, `GET` antigo → 404 e WebSocket com `Origin` estranho → 403.
4. Verificações finais: `lint-imports` (4 contratos), `ruff`, `pytest --cov` (95,6 %), piso por arquivo, `alembic check`, `tsc`, Vitest, `npm run build` e `npm audit`.

---

## 6. O que ficou de fora (e por quê)

### Exige decisão de produto ou da equipe
- **Catálogo fechado de `natureza`:** o registro público aceita natureza personalizada por desenho. O XSS foi resolvido na saída (escape + CSP), não na entrada.
- **Comunicações públicas antigas:** foram gravadas como o usuário `agente` e não há como distingui-las com segurança. Ficam com `origem = POLICIAL`, continuam corrigíveis pelo agente e **não têm código de acompanhamento**, então não são consultáveis pela nova rota pública.
- **Consolidação dos três `scripts/cadastrar_*.py`** (1.357 linhas que chamam a API do GitHub Projects): é preciso decidir qual lista de issues é a canônica.
- **Atualizar `docs/DOCUMENTACAO_DE_ENGENHARIA.md` e os diagramas** com os comportamentos novos: papel `CIDADAO`, código de acompanhamento, origem da ocorrência, "comunicação pública não é devolvida", credencial de rastreador e hash v2. Recomendo registrar como DECs. O AGENTS.md define esse documento como fonte única da verdade, e a mudança cabe à equipe.
- **Diagramas só em PNG → `.puml`:** reescrever ~20 diagramas está fora do escopo de correção de código.

### Mudanças arquiteturais maiores (recomendadas, não feitas)
- **Outbox de eventos** (§3.1.5): e-mails e eventos WS continuam publicados após o commit, dentro da requisição.
- **Enum `OperacaoAuditoria`** (§3.1.4): os literais de `operacao` seguem espalhados pelos casos de uso.
- **Quebra das páginas grandes do frontend** (`InqueritosPage`, `MedidasProtetivasPage`, `TrilhaAuditoriaPage`, `ComunicacaoInteragenciasPage`, `OcorrenciaDetalhe`).
- **Geocodificação pelo backend** (porta `Geocodificador` com cache e rate limit): só é necessária se a busca de endereço voltar à UI.
- **Credencial de rastreador com revogação individual:** a versão HMAC revoga em bloco, trocando o segredo. Uma tabela de dispositivos permitiria revogar uma viatura só.
- **Limitadores em memória:** não funcionam com várias réplicas da API (Redis ou similar).

### Itens da análise anterior que esta rodada não cobriu
Esses itens estavam na `ANALISE_TECNICA.md` (§2.1, §3, §4 e §5) e não entraram no Top 10 nem nos achados N:
- arquivo órfão de evidência quando o commit falha;
- auditoria de correção sem diff completo;
- `revisada_por_id`;
- filtro de interagências em Python após o `LIMIT`;
- heatmap contando `EXCLUIDA`/`REJEITADA`;
- N+1 em inquéritos;
- projeção leve para listagens;
- downgrade da `0001` apagando a auditoria;
- negação de papel não auditada fora do HTTP;
- gravidade na fila do Delegado;
- notificação ao agente autor;
- política de senha, *timing* de login e *password spraying*;
- lacunas do Cypress em módulos extras;
- seed sem PERITO/SUPERVISOR;
- demais métodos > 35 linhas.

### Deliberadamente não alterado
- **UP042** (`(str, Enum)` → `StrEnum`): muda o `str()` dos membros em todo o domínio e precisa de uma migração própria.
- **`pytest-randomly`:** não adicionado nesta rodada (o N1, que era pré-requisito, foi corrigido).

---

## 7. Atenção ao aplicar (mudanças de comportamento)

1. **Rode `uv run alembic upgrade head`** (migrações `0012`–`0016`) em cada ambiente. A `0015` falha de propósito se houver viatura com duas ordens ativas.
2. **API pública mudou:** `GET /v1/ocorrencias/publico/{protocolo}` foi removido. Use `POST /v1/ocorrencias/publico/consulta` com `{protocolo, codigo_acompanhamento}`.
3. **Produção:**
   - a aplicação **não sobe** com configuração insegura (ver N11);
   - a telemetria exige `TELEMETRIA_SEGREDO_DISPOSITIVOS` e credencial por viatura;
   - o simulador fica desabilitado;
   - `/docs` sai do ar.
4. **Notificações de papel/difusão** voltam a aparecer como não lidas uma vez, porque a leitura agora é por usuário.
5. **Alerta manual de medida protetiva:** o e-mail informado precisa estar cadastrado em algum envolvido da ocorrência.
6. **WebSocket:** clientes de origem fora do CORS são recusados, e cada sessão só recebe os eventos que pode ler.
7. **Dependências novas:**
   - backend: `pyjwt` (produção) e `httpx2` (dev); `python-jose` foi removido;
   - frontend: `react-router-dom@7` e `vitest` (dev).
