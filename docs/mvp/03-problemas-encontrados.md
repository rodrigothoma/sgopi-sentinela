# 03 — Problemas Encontrados (não previstos na documentação original)

Problemas identificados **durante a implementação** que não constam na Documentação de Engenharia. Cada item traz impacto, evidência e a decisão adotada (ou pendente). Os IDs (`P01`…) são referenciados nos demais documentos e em comentários do código.

Legenda de severidade: 🔴 bloqueia/compromete o MVP · 🟠 deve ser resolvido antes de produção · 🟡 limitação conhecida, aceitável no MVP.

---

## Especificação e escopo

### P01 🔴 Stack contraditória entre documentos e prompt
- **Achado:** a Seção 4.3 da especificação define **Python + FastAPI + Firebase Firestore**; o `README.md` define **Python + FastAPI + PostgreSQL/SQLAlchemy**; o prompt de implementação exige **React + Next.js**. Três fontes, três respostas. A Seção 7.1 ainda cita `pytest`/`unittest.mock`/Selenium, e a Seção 4.2 cita "JPA / Hibernate" (resquício da stack Java original).
- **Impacto:** a equipe pode desenvolver em pilhas diferentes; as ferramentas de teste documentadas não se aplicam.
- **Decisão:** seguir o prompt (React + Next.js/TypeScript). **Pendente:** a equipe deve atualizar a Seção 4.3, o README e a Seção 7.1 (vitest/Playwright no lugar de pytest/Selenium) ou reverter a decisão.

### P02 🟠 Máquina de estados com nomes inconsistentes
- **Achado:** Seção 3.2: `Rascunho → Aguardando Revisão → Validada / Rejeitada → Em Despacho → Concluída`. UC04 usa `Em Correção` (não `Rejeitada`) e prevê retorno ao Agente; UC02 usa `Em Atendimento` (não `Em Despacho`); UC01 RN3 diz que toda ocorrência nasce **compulsoriamente** em `Aguardando Revisão`, o que torna `Rascunho` inalcançável.
- **Decisão:** adotar os nomes dos casos de uso (mais específicos) e eliminar `Rascunho`: `AGUARDANDO_REVISAO ⇄ EM_CORRECAO`, `AGUARDANDO_REVISAO → VALIDADA → EM_ATENDIMENTO → CONCLUIDA`. Implementado em `src/core/domain/ocorrencia/StatusOcorrencia.ts` com transições explícitas e testadas. **Pendente:** alinhar a Seção 3.2.

### P16 🟡 Despacho múltiplo (UC02 Alt. I) conflita com a máquina de estados
- **Achado:** UC02 Cenário Alternativo I permite "mais de uma viatura de apoio", mas após o primeiro despacho a ocorrência vai para `EM_ATENDIMENTO` e a RN2 (`somente VALIDADA pode ser despachada`) bloqueia o reforço.
- **Decisão:** MVP implementa 1 viatura por ordem. Para reforço, o domínio precisará de um comando `reforcar` permitido em `EM_ATENDIMENTO`. Registrado na Fase 8 do plano.

### P17 🟡 "Transmitir a ordem ao terminal da viatura" não tem receptor
- **Achado:** UC02 passo 8 pressupõe um terminal embarcado; não há ator/tela definidos para ele.
- **Decisão:** o evento `viatura.despachada` é publicado no SSE e pode ser consumido por um futuro app de viatura. Sem UI no MVP.

### P11 🟡 "Assinar digitalmente o ato de validação" (UC04 passo 8) sem infraestrutura de certificados
- **Decisão:** implementado como **hash SHA-256 de integridade** (`hashIntegridade`) que sela a narrativa e bloqueia edição direta (RN2). Assinatura ICP-Brasil exige certificado/HSM — ciclo futuro.

### P14 🟡 Upload de evidências: UC01 pede upload, Seção 3.2 exclui mídia pesada
- **Decisão:** o MVP grava **metadados + hash** (nome, MIME, tamanho, SHA-256) e valida formato (`.pdf/.jpg/.png`). Sem o binário, o hash é calculado sobre `nome:tamanho` (fraco); com o adaptador de *storage* passará a ser o hash do conteúdo. A porta já existe (`PortaHash`).

---

## Next.js / plataforma

### P03 🔴 Route Handlers do Next.js não suportam servidor WebSocket
- **Achado:** a especificação exige "WebSockets (STOMP/SockJS)". STOMP/SockJS são artefatos do ecossistema Spring (stack Java original). Route Handlers não expõem o `http.Server` para *upgrade*; WS exigiria `server.js` customizado, perdendo otimizações e complicando deploy.
- **Decisão:** **Server-Sent Events** (`GET /api/eventos`) para o fluxo servidor→cliente (posições, mudanças de status, despachos) e REST para cliente→servidor. Atende ao critério "< 1 s sem refresh" (medido < 100 ms local). Reconexão automática do `EventSource` + recarga de estado ao reconectar. Cabeçalho `X-Accel-Buffering: no` para proxies. **Pendente:** atualizar RNF01/Seção 4.3 para "SSE (ou WebSocket em serviço dedicado)".

### P04 🔴 `instanceof` falha entre chunks do Turbopack (build de produção)
- **Achado:** em `next start`, `ErroNaoAutorizado` lançado pelo caso de uso (chunk `src_config_container_ts`) não era reconhecido por `erro instanceof DomainError` no route handler (chunk `[root-of-the-server]`): a classe foi **duplicada** em bundles distintos. Resultado: 500 "Erro interno" em vez de 403. Reproduzido no smoke test; não ocorre em `vitest`.
- **Decisão:** marca global com `Symbol.for("sgopi.DomainError")` e função `ehErroDominio()`; **nenhum `instanceof` de classes de domínio fora do núcleo**. Erros Zod detectados também por `name === "ZodError"`. Verificado em dev e prod.

### P05 🟠 `next start` exige `SESSION_SECRET` — e isso não estava documentado
- **Achado:** o adaptador de sessão recusa iniciar em produção sem segredo (decisão de segurança), o que fez o primeiro smoke test falhar com 500.
- **Decisão:** manter a exigência; documentar em `.env.example`, no README e no plano. Em `dev` há fallback inseguro com aviso.

### P06 🟠 Singletons em memória × HMR e múltiplos módulos
- **Achado:** o Next.js (dev) recarrega módulos e pode avaliar `container.ts` mais de uma vez; sem cuidado, cada rota teria seu próprio repositório e seu próprio simulador GPS (posições duplicadas, dados divergentes).
- **Decisão:** instância única em `globalThis[Symbol.for("sgopi.container")]` e *bootstrap* via `instrumentation.ts` (`register()` no runtime `nodejs`). Verificado em dev: 1 simulador, 10 eventos/5 s para 5 viaturas.

### P10 🟠 Leaflet não roda em SSR e seus ícones padrão quebram em bundlers
- **Achado:** `leaflet` acessa `window` na importação → erro em Server Components. Os ícones PNG padrão (`marker-icon.png`) não são resolvidos por Turbopack/webpack sem configuração.
- **Decisão:** `next/dynamic(..., { ssr: false })` para `MapaTatico`, `import("leaflet")` dentro de `useEffect`, marcadores via `circleMarker`/`divIcon` (sem assets). CSS importado do pacote.

### P18 🟡 Política de uso dos tiles do OpenStreetMap
- **Achado:** `tile.openstreetmap.org` proíbe uso pesado/produção sem provedor próprio e exige `User-Agent`/atribuição.
- **Decisão:** aceitável para demonstração acadêmica; produção deve usar provedor (MapTiler, Stadia, servidor próprio). O fallback tabular (RNF04) é acionado quando ≥ 4 tiles falham sem nenhum carregado — heurística, ajustar conforme provedor.

### P19 🟡 Next 16: `params`/`cookies()` assíncronos e `middleware.ts` renomeado para `proxy.ts`
- **Decisão:** todo `params` é `await`ado; sessão lida com `await cookies()`; não se usou middleware (guarda nos layouts/handlers), evitando a mudança de nome.

---

## Persistência e consistência

### P07 🟠 Despacho grava 3 agregados sem transação
- **Achado:** `DespacharViatura` persiste ordem, viatura e ocorrência em sequência. Com repositório em memória é efetivamente atômico, mas com banco real uma falha intermediária deixa estado parcial (ex.: viatura `EM_DESLOCAMENTO` e ocorrência `VALIDADA`).
- **Decisão:** ordem de gravação escolhida para minimizar dano (ordem → viatura → ocorrência) e comentário no código. **Pendente:** porta `UnidadeDeTrabalho` (transação) ao adotar o SGBD.

### P08 🟠 Firestore é inadequado para dois requisitos centrais
- **Achado:** (a) `proximoProtocolo` precisa de contador **sequencial atômico** por ano; (b) o log de auditoria precisa de **ordem total** e escrita *append-only*. Firestore exige `runTransaction`/contadores distribuídos e não oferece garantia nativa de imutabilidade (regras de segurança podem negar UPDATE/DELETE, mas o Admin SDK as ignora).
- **Decisão:** recomendação de **PostgreSQL** (sequência + tabela com trigger *no update/delete*). Se a equipe mantiver Firestore, documentar as transações e proteger o log com hash-chain (já implementado) + exportação periódica para WORM.

### P09 🟡 Dados voláteis e protocolo reiniciável
- **Achado:** o repositório em memória perde tudo ao reiniciar; o contador `BO-AAAA-NNNNNN` recomeça em 1 → **protocolos duplicados entre reinícios**.
- **Decisão:** aceitável para demonstração; **não** usar em homologação com dados reais. Primeiro item técnico da Fase 7.

### P20 🟡 Validade do GPS calculada no cliente depende do relógio do navegador
- **Achado:** o painel reavalia `sinalGpsValido` a cada 1 s comparando `recebidaEm` (relógio do servidor) com `Date.now()` do navegador. Desvio > 60 s marcaria toda a frota como sem sinal.
- **Decisão:** o servidor continua sendo a fonte de verdade (o caso de uso recalcula no despacho); o cliente apenas antecipa o aviso. Mitigação futura: enviar `agoraServidor` no evento `conectado` e usar o *offset*.

---

## Segurança e privacidade

### P13 🟠 PII em texto claro e potencial vazamento em logs
- **Achado:** CPF dos envolvidos é armazenado em claro; a especificação só trata de ocultação no portal público (RF08).
- **Decisão:** o log de auditoria **não** recebe PII (só ids, contagens e hashes — verificado nos casos de uso). **Pendente:** criptografia em repouso do campo `documento`, mascaramento em qualquer exportação, base legal LGPD documentada.

### P15 🟠 Autenticação de demonstração
- **Achado:** usuários *seed* com senha comum (`sgopi123`), hash SHA-256 sem *salt*, sessão de 8 h sem revogação, sem MFA.
- **Decisão:** adequado apenas ao MVP. Mensagem de erro genérica ("Matrícula ou senha inválidos") para evitar enumeração de usuários; tentativas falhas auditadas. Substituir por OIDC/LDAP + `argon2` antes de qualquer piloto.

### P21 🟡 Endpoint de telemetria autenticado por token estático
- **Decisão:** `x-telemetria-token` suficiente para simuladores; hardware real deve usar mTLS ou token por viatura com rotação.

---

## Processo

### P12 🟡 Ferramentas de teste da Seção 7.1 não se aplicam à stack
- **Decisão:** `vitest` para o núcleo (46 testes, sem servidor nem banco — exatamente o objetivo declarado da Seção 7.1) e **Playwright** (em vez de Selenium) para E2E do fluxo do MVP (Fase 7).

### P22 🟡 Verificação visual do mapa não realizada nesta iteração
- **Achado:** o ambiente de implementação não possuía navegador. O build compila `MapaTatico` sem erros e o HTML do painel é servido (200) com o *placeholder* "Carregando mapa…", mas a renderização dos marcadores Leaflet e o fallback por falha de tiles não foram observados visualmente.
- **Decisão:** primeiro passo da Fase 7.

---

## Resumo por severidade

| Sev. | IDs |
| :-: | :--- |
| 🔴 | P01, P03, P04 |
| 🟠 | P02, P05, P06, P07, P08, P10, P13, P15 |
| 🟡 | P09, P11, P12, P14, P16, P17, P18, P19, P20, P21, P22 |
