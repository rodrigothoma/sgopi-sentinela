# Análise Técnica (revisão 2) — SGOPI Sentinela

> Feita em 05/10/2026 no branch `matheus-Fastapi` (commit `6e213a3`). Ela complementa a `ANALISE_TECNICA.md` anterior, feita no commit `09eaec1`.
>
> Esta revisão:
> 1. roda de novo as verificações obrigatórias e mais algumas (`alembic check`, `ruff`, `npm audit`);
> 2. traz **achados novos**;
> 3. confere se os achados anteriores **continuam valendo**, corrigindo referências de linha que estavam erradas.
>
> Os caminhos de backend são relativos a `backend/src/`, salvo indicação contrária.

---

## 0. Resumo executivo

### 0.1 Verificações

| Verificação | Resultado |
|---|---|
| `lint-imports` (AGENTS.md §6) | ✅ 3 contratos mantidos, 0 violações |
| `pytest --cov` (AGENTS.md §6) | ⚠️ 636 passaram e 13 E2E foram pulados. A cobertura de `domain/` + `application/` é **93%**. Porém **um teste é intermitente** e falhou na primeira execução (ver N1) |
| `tsc --noEmit` (AGENTS.md §6) | ✅ sem erros |
| `npm run build` (AGENTS.md §6) | ⚠️ passa, mas o bundle único tem **941 kB** (284 kB gzip) e gera aviso de chunk |
| `alembic check` (extra) | ❌ **falha**: os índices de `comunicacoes_interagencias` divergem dos modelos |
| `ruff check` (extra, regras padrão + config) | ⚠️ 487 apontamentos, dos quais 100 são corrigíveis automaticamente |
| `npm audit --omit=dev` (extra) | ⚠️ 2 vulnerabilidades moderadas em `react-router`/`react-router-dom` 6.30.6 |

### 0.2 Mudanças desde a análise anterior

Os dois commits novos, `1915ca0` e `6e213a3`, tratam da revalidação de integridade das evidências. Eles **não corrigem** nenhum dos achados críticos ou altos da análise anterior: os 10 itens prioritários continuam presentes no código (ver §2).

### 0.3 Top 10 prioridades atualizado

| # | Sev. | Achado | Origem |
|---|---|---|---|
| 1 | 🔴 Crítica | XSS armazenado no popup Leaflet das áreas de risco (`natureza` livre, aceita no registro público) | anterior, confirmado |
| 2 | 🔴 Crítica | O registro público grava a ação como o usuário real `agente`, que vira autor e pode corrigir o registro | anterior, confirmado |
| 3 | 🔴 Alta | O WebSocket transmite todos os eventos (com PII) a todos os clientes e só valida o token no handshake | anterior, confirmado |
| 4 | 🔴 Alta | Notificações: o flag `lida` é compartilhado, e não há checagem de posse ao marcar como lida | anterior, confirmado |
| 5 | 🔴 Alta | O download de laudo procura o arquivo pela chave errada e devolve bytes falsos | anterior, confirmado |
| 6 | 🔴 Alta | Enumeração de ocorrências pelo protocolo público sequencial | anterior, confirmado |
| 7 | 🟠 Alta | Corrida entre despacho de apoio e encerramento (a ocorrência não é salva, então `versao` não é checada) | anterior, confirmado |
| 8 | 🟠 Média | **Validação ausente na borda** do alerta tático: papel e criticidade são `str` livres. É a causa raiz do bug `OPERADOR` | **novo (N3)** |
| 9 | 🟠 Média | **A verificação automática de integridade** a cada abertura do detalhe relê os arquivos e grava auditoria a cada evidência | **novo (N4)** |
| 10 | 🟠 Média | **Divergência de migração confirmada** por `alembic check`, sem checagem no CI; **teste intermitente** na suíte | **novo (N1, N2)** |

---

## 1. Achados novos

### N1. Teste intermitente na autenticação pública de documentos (Média)
- **Onde:** `backend/tests/integration/test_publico_http.py:48`.
- **Problema:** o teste checa `"789" not in r.text` para garantir que o CPF `123.456.789-09` não vaza. Só que a resposta contém valores aleatórios:
  - o `hash_integridade` (64 caracteres hex);
  - os microssegundos de `emitido_em`.
- **Evidência:** na primeira execução desta análise, o hash `789c0169dee4…` fez o teste falhar. A probabilidade estimada de falha é de **~2–3% por execução**, ou seja, o CI vai falhar de vez em quando sem motivo real.
- **Correção:**
  - verificar o documento completo (`"123.456.789-09" not in r.text`) e o nome;
  - ou checar campos específicos do JSON em vez de buscar substring no corpo inteiro.

### N2. Divergência entre modelos e migrações, sem checagem no CI (Média)
- **Evidência:** `alembic upgrade head && alembic check` em um SQLite limpo detecta 4 operações pendentes:

  | Situação | Índice |
  |---|---|
  | No banco, mas não no modelo | `ix_comunicacoes_interagencias_origem` |
  | No banco, mas não no modelo | `ix_comunicacoes_interagencias_protocolo` |
  | No modelo, mas não no banco | `ix_comunicacoes_interagencias_departamento_origem` |
  | No modelo, mas não no banco | `ix_comunicacoes_interagencias_protocolo_ocorrencia` |

- **Causa:** a migração `0011` dá nomes diferentes dos do modelo. A análise anterior classificou isso como "Baixa"; agora o problema está **confirmado**, e o próximo `alembic revision --autogenerate` vai misturar essa correção com mudanças sem relação.
- **Correção:** criar uma migração `0012` que renomeie os índices e adicionar um passo `uv run alembic check` ao CI.

### N3. O alerta tático não valida nada na borda HTTP (Média)
- **Onde:** `adapters/inbound/http/v1/inteligencia_router.py:43-51` (`AlertaCriticidadeRequest`). Os campos `nivel_criticidade: str = "CRITICA"` e `papel_destinatario: str | None` são texto livre, e `latitude`, `longitude` e `raio_metros` não têm limites.
- **Efeito:** o frontend envia `'OPERADOR'` (`pages/PainelTaticoPage.tsx:83`), papel que não existe. A API aceita o valor em silêncio, e a notificação não chega a ninguém. Por isso o bug passou despercebido.
- **Correção:**
  - tipar com `Papel | None` e um Enum `NivelCriticidade`;
  - aplicar `Field(ge=-90, le=90)` às coordenadas e `gt=0` ao raio;
  - no frontend, derivar as opções do tipo `Papel` (`types/api.ts:2`) e mover os rótulos para o i18n, pois hoje estão fixos em português.

### N4. A revalidação automática de integridade é cara e infla a auditoria (Média)
- **Onde:** `components/ocorrencias/OcorrenciaDetalhe.tsx:52-56` (`useEffect` → `verificarIntegridade`) e `application/use_cases/ocorrencia/acessar_evidencia.py:74-95`.
- **Problema:** cada vez que alguém abre o detalhe de uma ocorrência, **cada evidência**:
  - é lida inteira do disco (até 10 MB);
  - tem o SHA-256 recalculado;
  - gera **um registro em `registros_auditoria`**, tabela append-only que não pode ser limpa.

  Uma ocorrência com 20 evidências, aberta 50 vezes por dia, gera 1.000 registros e cerca de 10 GB de leitura por dia. A remontagem por StrictMode ou pela troca de aba repete tudo.
- **Correção:**
  - fazer a verificação automática **sem auditoria**, ou com resultado em cache por hash e mtime durante N minutos;
  - auditar só a verificação **solicitada** (botão "Verificar novamente") e o download;
  - outra opção é paginar e verificar sob demanda.
- **Detalhes no mesmo fluxo:**
  - `IntegridadeEvidenciaOutput.verificado_em` é `str` (`ports/inbound/interface_acessar_evidencia.py:18`), e a camada de aplicação faz `isoformat()`. O DTO deveria ter `datetime` e a serialização deveria ficar na borda.
  - `EstadoIntegridadeEvidencia` continua sem `ARQUIVO_AUSENTE`, embora esse valor seja gravado na auditoria (`acessar_evidencia.py:81`).

### N5. Canonicalização ambígua no `hash_narrativa` (Baixa → Média, RNF03)
- **Onde:** `domain/ocorrencia/entity.py:494-499`. Os campos são unidos com `"\n"` e os envolvidos com `"|"`, sem escape.
- **Problema:** textos diferentes podem produzir o mesmo hash, deslocando conteúdo entre campos. Por exemplo, `descricao="a\nb", localizacao="c"` e `descricao="a", localizacao="b\nc"` geram a mesma entrada. O mesmo vale para um `|` no nome de um envolvido. Além disso, as evidências (`hash_sha256`) e os itens apreendidos ficam fora do hash do documento oficial.
- **Correção:**
  - serializar em JSON canônico (`json.dumps(..., sort_keys=True, ensure_ascii=False, separators=(",", ":"))`);
  - incluir os hashes das evidências;
  - registrar `hash_versao` na ocorrência para que os documentos já emitidos continuem verificáveis com o algoritmo v1.

### N6. Bundle sem divisão de código (Média, desempenho)
- **Onde:** `frontend/src/App.tsx:1,35`. Existe um `<Suspense>`, mas nenhuma rota usa `React.lazy`.
- **Efeito:** o bundle tem 941 kB, e o cidadão que só abre `/registrar-cidadao` ou `/autenticar` baixa Leaflet e todas as páginas internas, incluindo `InqueritosPage` (1.311 linhas) e `MedidasProtetivasPage` (998 linhas).
- **Correção:** usar `lazy(() => import(...))` por rota e `manualChunks` para `leaflet`.

### N7. Dependência do frontend com advisories (Baixa)
- **Onde:** `react-router-dom@6.30.6`.
- **Advisories:**
  - GHSA-wrjc-x8rr-h8h6: open redirect via `\` em `<Link>`/`useNavigate`;
  - GHSA-337j-9hxr-rhxg: só afeta SSR.
- **Exposição:** baixa, porque nenhum `navigate` usa destino vindo da URL.
- **Correção:** acompanhar a correção na linha 6.x ou planejar a migração para a v7, e adicionar `npm audit --omit=dev --audit-level=high` ao CI.

### N8. Geocodificação envia o local do crime a um terceiro (Média, LGPD)
- **Onde:** `frontend/src/services/geocodificacaoService.ts:6`, chamado em `components/ocorrencias/LocalOcorrencia.tsx:45,62`.
- **Problema:** o navegador do agente envia o endereço e as coordenadas do fato direto ao `nominatim.openstreetmap.org`. Isso tem três consequências:
  - o dado operacional sai do perímetro do sistema sem base legal declarada;
  - a política do Nominatim (1 req/s, identificação, sem uso intensivo) não é garantida;
  - não há cache.
- **Correção:**
  - rotear por uma porta `Geocodificador` no backend, com instância própria ou provedor contratado, rate limit e cache;
  - no mínimo, tornar a busca uma ação explícita do usuário e documentar a decisão (DEC).

### N9. Higiene de código detectada pelo `ruff` (Baixa)
| Regra | Qtde | Observação |
|---|---|---|
| `F401` imports não usados | 16 | Incluem `domain/interagencias/entity.py:15`, `domain/notificacao/entity.py:14`, `revisar_ocorrencia.py:8` e o import morto de `infrastructure.di` em `laudos_router.py:197` |
| `I001` imports desordenados | 63 | Corrigível com `--fix` |
| `DTZ005`/`DTZ011` `datetime.now()`/`date.today()` sem fuso | 6 | Confirma o achado anterior sobre datetimes naive no domínio |
| `RUF100` `noqa` inúteis | 12 | — |
| `B008` `Depends()` em default | 376 | Falso positivo no FastAPI; desligar via `extend-immutable-calls` |

Há ainda imports no meio do arquivo com `# noqa: E402` em `ocorrencias_router.py:281+`. O arquivo, com 560 linhas, deveria ser dividido em `ocorrencias_publico_router`, `evidencias_router` e `revisao_router`.

**Recomendação:** adotar `ruff` no `pyproject.toml` com essas regras e rodá-lo no CI.

### N10. Buracos de cobertura escondidos pela média de 93% (Média)
| Módulo | Cobertura |
|---|---|
| `application/use_cases/inquerito/vincular_ocorrencias.py` | **22%** |
| `application/use_cases/inquerito/buscar_conexoes.py` | **43%** |
| `domain/inquerito/entity.py` | 78% |
| `domain/usuario/entity.py` | 82% |

Os dois primeiros são exatamente os métodos de 86 e 92 linhas apontados na análise anterior.

**Recomendação:** exigir um piso de cobertura **por arquivo** para `domain/` (ex.: 85%), não só o agregado.

### N11. Travas de demonstração: refinamento do achado anterior
- **Orquestrador:** a análise anterior dizia que ele não tinha trava. Na verdade, ele só liga com `despacho_automatico_ligado=True` (`viaturas_router.py:112`; padrão `False`, em `settings.py:63`). O gerador de ocorrências também é opt-in (`main.py:34`).
- **O que falta:** um *fail-fast* em `Settings._validar_seguranca` (`infrastructure/config/settings.py:96-106`) que **recuse** `despacho_automatico_ligado`, `gerador_ocorrencias_ligado` e o endpoint do simulador quando `is_production`.
- **Esse mesmo validador também deveria recusar:**
  - `database_url` com a senha padrão `admin`;
  - CORS com `localhost`;
  - `smtp_usar_tls=False`.

### N12. Telemetria sem identidade de dispositivo (Média)
- **Onde:** `POST /v1/telemetria/posicoes` (`viaturas_router.py:88-91`) aceita a posição de **qualquer** viatura vinda de qualquer `OPERADOR_CENTRAL`/`SUPERVISOR`.
- **Efeito:** um token humano pode "teletransportar" uma viatura até a ocorrência e disparar `viatura.chegada_ao_local` (`registrar_posicao_viatura.py:68-95`), que muda a situação e audita com `quem=None`.
- **Correção:** criar uma credencial de dispositivo por viatura (papel técnico `TELEMETRIA` ou token por viatura), vincular `viatura_id` ao token e auditar a origem.

### N13. `python-jose`: refinamento
- **Situação atual:** o `uv.lock` fixa `python-jose 3.5.0`, versão que corrige as CVEs de 2024 (CVE-2024-33663/33664).
- **Risco remanescente:**
  - a biblioteca tem pouca manutenção;
  - a dependência `ecdsa 0.19.2` tem a CVE-2024-23342 sem correção. Ela não afeta HS256, mas fica na árvore.
- **Conclusão:** a migração para `PyJWT` continua recomendada, com prioridade **média**, e não "alta".

---

## 2. Achados da análise anterior: situação atual

Todos os itens abaixo foram **reconferidos no código atual**. Várias referências de linha do documento anterior estavam erradas: por exemplo, `deps.py:131` aponta para um arquivo de 99 linhas, e `main.py:234` para um de 123. Por isso, a coluna "Local correto" substitui essas referências.

| Achado anterior | Situação | Local correto |
|---|---|---|
| XSS no popup das áreas de risco | ❌ Persiste | `frontend/src/components/painel/MapaTatico.tsx:185-211` |
| Registro público como usuário `agente` | ❌ Persiste | `adapters/inbound/http/v1/ocorrencias_router.py:141-145` (o `import uuid4` dentro da função gera erro de FK) |
| Enumeração por protocolo público | ❌ Persiste | `ocorrencias_router.py:172-185` |
| WebSocket sem filtro/reautenticação | ❌ Persiste | `adapters/inbound/websocket/tempo_real_router.py:28-44` (sem checagem de `Origin`; o `Ator` é descartado na linha 31) |
| Broadcast WS desalinhado (`zip` após `await`) | ❌ Persiste | `adapters/inbound/websocket/gerenciador_conexoes.py:44-45` |
| `MarcarNotificacaoLida` sem checagem de posse | ❌ Persiste | `application/use_cases/notificacao/gerir_notificacoes.py:54-59` |
| Download de laudo com bytes falsos | ❌ Persiste | `adapters/inbound/http/v1/laudos_router.py:197-208` |
| SMTP `starttls()` sem contexto SSL | ❌ Persiste | `adapters/outbound/email/enviador_email_smtp.py:75` |
| Token válido após desativar usuário | ❌ Persiste | `adapters/inbound/http/deps.py:38-43` (`extrair_ator` não consulta `ativo`) |
| Validação fraca de segredo em produção | ❌ Persiste | `infrastructure/config/settings.py:96-106` |
| `X-Request-ID` sem validação + hack com `locals()` | ❌ Persiste | `adapters/inbound/http/middleware.py:18` e `:27` |
| CORS com `allow_credentials` e `*` | ❌ Persiste | `main.py:56-63` |
| `/docs` público em produção | ❌ Persiste | `main.py:48-53` |
| Corrida no despacho de apoio | ❌ Persiste | `application/use_cases/despacho/despachar_viatura.py:102-114` |
| `datetime.now()` naive no domínio | ❌ Persiste | `domain/medida_protetiva/entity.py:56`, `domain/notificacao/entity.py:53,90`, `domain/interagencias/entity.py:69,114` |
| Opção `'OPERADOR'` inexistente | ❌ Persiste | `frontend/src/pages/PainelTaticoPage.tsx:83` (causa raiz em N3) |
| Namespace i18n `interagencias` ausente | ❌ Persiste | `frontend/src/i18n.ts`; não existe `locales/*/interagencias.json` |
| Divergência de índices na migração `0011` | ❌ Persiste, agora **comprovado** | ver N2 |
| `pyproject.toml`/`uv.lock` órfãos na raiz | ❌ Persiste | `pyproject.toml` (`requires-python >=3.14`, sem dependências) |
| Três scripts de issues sobrepostos | ❌ Persiste | `scripts/cadastrar_*.py` |
| Diagramas só em PNG | ❌ Persiste | `docs/diagramas/`: 20 PNG e 1 `.puml` |
| README com contagem de testes desatualizada | ❌ Persiste | `README.md:132` (diz 613; hoje são 649 coletados) |
| Aviso de depreciação `starlette.testclient` + `httpx` | ❌ Persiste e é **suprimido** | `backend/pyproject.toml` (`filterwarnings`), mas ainda aparece em `tests/integration/test_tempo_real_ws.py:11` |
| `python-jose` "com CVEs" | ⚠️ Refinado | ver N13 |
| Orquestrador "sem trava" | ⚠️ Refinado | ver N11 |

Os demais itens da análise anterior que não estão na tabela (§2.1, §2.2, §3, §4 e §5) não foram afetados pelos commits recentes e continuam valendo como estavam descritos.

---

## 3. O que pode ser melhorado

### 3.1 Arquitetura e código
1. **Validação na borda com tipos de domínio.** Os schemas Pydantic deveriam usar os Enums (`Papel`, `StatusOcorrencia`, `NivelCriticidade`), e não `str`. Isso elimina uma classe inteira de bugs silenciosos (N3).
2. **Routers enxutos.** Quebrar `ocorrencias_router.py` (560 linhas) e remover os imports com `E402`. No frontend, quebrar as páginas acima de 400 linhas (`InqueritosPage`, `MedidasProtetivasPage`, `TrilhaAuditoriaPage`, `ComunicacaoInteragenciasPage`, `OcorrenciaDetalhe`) em componentes e hooks.
3. **Contrato de camadas mais estrito.** Hoje `adapters` pode importar qualquer coisa de `infrastructure`. Um contrato `forbidden` que permita só `infrastructure.di` (getters) e `infrastructure.config` evitaria casos como o de `laudos_router.py:197`.
4. **Auditoria proporcional.** Separar "leitura de rotina" de "ato auditável" (N4) e reunir os literais de `operacao` em um Enum `OperacaoAuditoria`.
5. **Outbox de eventos.** Hoje e-mails e eventos WS são publicados depois do `commit`, mas dentro da requisição. Uma tabela outbox processada em background resolve ao mesmo tempo as corridas, as perdas e a latência.

### 3.2 Qualidade e CI
1. Adicionar ao CI:
   - `ruff check`;
   - `alembic check`;
   - `npm audit --audit-level=high`;
   - `pip-audit` (contra o `uv.lock` exportado);
   - um job com **service Postgres 16** para exercitar os triggers append-only e os `ON CONFLICT`.
2. Usar `pytest-randomly` ou `-p randomly` para expor dependência de ordem, e corrigir o N1 antes.
3. Introduzir Vitest no frontend, começando por `utils/*` e pelo backoff do `ClienteTempoReal`.
4. Adotar um piso de cobertura por arquivo (N10).

### 3.3 Segurança e LGPD
1. Tratar os itens 1 a 7 do Top 10 (todos herdados da análise anterior e ainda abertos).
2. Endurecer o `Settings` em produção (N11).
3. Criar uma identidade de dispositivo para a telemetria (N12).
4. Levar a geocodificação para o backend (N8).
5. Adotar uma Content-Security-Policy no frontend (`script-src 'self'`, `img-src` com os tiles OSM) como defesa em profundidade contra o XSS do item 1.

### 3.4 Frontend e UX
1. Divisão de código por rota (N6).
2. i18n completo: o namespace `interagencias` e os rótulos fixos em português do Painel Tático (`PainelTaticoPage.tsx:73-84`).
3. Trocar os `window.confirm` (`FilaDelegadoPage.tsx:83,108`) por um modal acessível, consistente com os modais novos.
4. Na tela de evidências, mostrar o estado "verificado há X min" em vez de verificar automaticamente a cada abertura (N4).

---

## 4. Roteiro sugerido (atualizado)

| Fase | Itens |
|---|---|
| **Imediato (≤ 1 dia)** | N1 (teste intermitente); N2 (migração `0012` + `alembic check` no CI); N3 (Enums no `AlertaCriticidadeRequest` + corrigir `'OPERADOR'`) |
| **Sprint 1: segurança** | Itens 1 a 6 do Top 10; N11 (fail-fast de produção); N12 (telemetria) |
| **Sprint 2: integridade** | Item 7 (corrida do despacho de apoio + índice "1 ordem ativa por viatura"); N4 (auditoria proporcional); N5 (hash canônico v2 com `hash_versao`); datetimes naive |
| **Sprint 3: qualidade** | `ruff` + Postgres no CI; N10 (testes de `vincular_ocorrencias`/`buscar_conexoes`); Vitest; quebra dos routers e páginas grandes |
| **Sprint 4: desempenho e LGPD** | N6 (code splitting); N8 (geocodificação no backend); N7/N13 (dependências) |

---

## Anexo: comandos usados

```bash
cd backend
PYTHONPATH=src uv run lint-imports --config pyproject.toml
uv run pytest --cov
DATABASE_URL=sqlite+aiosqlite:///<tmp>/check.db uv run alembic upgrade head && uv run alembic check
uv tool run ruff check src --statistics

cd ../frontend
npx tsc --noEmit && npm run build
npm audit --omit=dev
```
