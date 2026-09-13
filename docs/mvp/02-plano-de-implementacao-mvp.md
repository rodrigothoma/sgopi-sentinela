# 02 — Plano de Implementação do MVP

Passos ordenados para construir o MVP do SGOPI Sentinela em **React + Next.js** com **Arquitetura Hexagonal**. Cada passo indica o estado atual (✅ feito nesta iteração · 🔜 próximo · ⏳ ciclo futuro), o que produz e como verificar.

> Regra de ouro adotada em todos os passos: **`src/core` nunca importa `next`, `react`, `zod`, `leaflet` ou `node:*`.** Verifique com
> `grep -rE "from \"(next|react|zod|leaflet|node:)" src/core` — o resultado deve ser vazio.

---

## Fase 0 — Fundação do projeto ✅

| Passo | Ação | Verificação |
| :-: | :--- | :--- |
| 0.1 | Criar `package.json` com Next 16, React 19, TypeScript 5.9, Zod 4, Leaflet 1.9, Vitest 5 | `npm install` sem vulnerabilidades (`npm audit`) |
| 0.2 | `tsconfig.json` com `strict` e aliases `@/*` → `src`, `@app/*` → `app` | `npm run typecheck` |
| 0.3 | `vitest.config.mts` apontando apenas para `tests/**` (núcleo) | `npm test` |
| 0.4 | `.env.example` com `SESSION_SECRET`, `TELEMETRIA_TOKEN`, `GPS_SIMULADOR_*` | `next start` sem `SESSION_SECRET` falha propositalmente (P05) |
| 0.5 | `.gitignore` para Node/Next | `git status` limpo de `node_modules`/`.next` |

## Fase 1 — Núcleo de domínio (sem framework) ✅

| Passo | Ação | Arquivo(s) |
| :-: | :--- | :--- |
| 1.1 | Erros de domínio tipados por `codigo` (VALIDACAO, NAO_ENCONTRADO, TRANSICAO_INVALIDA, NAO_AUTORIZADO, PRE_CONDICAO) com marca `Symbol.for` (P04) | `src/core/domain/shared/DomainError.ts` |
| 1.2 | Objetos de valor: `Coordenada` (validação WGS-84) e `distanciaHaversineKm` | `src/core/domain/shared/Coordenada.ts` |
| 1.3 | Máquina de estados da ocorrência com transições explícitas (P02) | `src/core/domain/ocorrencia/StatusOcorrencia.ts` |
| 1.4 | Agregado `Ocorrencia` imutável: `registrar`, `validar`, `devolverParaCorrecao`, `corrigirEReenviar`, `iniciarAtendimento`, `concluir`; invariantes UC01 RN1–RN3, UC04 RN2–RN3 | `src/core/domain/ocorrencia/Ocorrencia.ts` |
| 1.5 | `Envolvido`, `EvidenciaDigital` (formatos aceitos UC01 Exceção II) | `src/core/domain/ocorrencia/*` |
| 1.6 | `Viatura` com `sinalGpsValido(agora)` (60 s — UC02 RN3), `despachar` (RN1), descarte de telemetria fora de ordem | `src/core/domain/viatura/Viatura.ts` |
| 1.7 | `OrdemDespacho` (registro imutável com modo AUTOMATICO/MANUAL) | `src/core/domain/despacho/OrdemDespacho.ts` |
| 1.8 | `RegistroAuditoria` com encadeamento por hash e serialização canônica | `src/core/domain/auditoria/RegistroAuditoria.ts` |
| 1.9 | `Papel` (RBAC) e `Usuario` | `src/core/domain/usuario/*` |

**Verificação:** `tests/domain/*.test.ts` (16 testes).

## Fase 2 — Aplicação: portas e casos de uso ✅

| Passo | Ação | Arquivo(s) |
| :-: | :--- | :--- |
| 2.1 | Portas de saída: repositórios, relógio, ids, hash, auditoria, publicador de eventos | `src/core/application/ports/outbound/*` |
| 2.2 | Portas de entrada (contratos dos casos de uso + DTOs) | `src/core/application/ports/inbound/CasosDeUso.ts` |
| 2.3 | Matriz RBAC e `Autorizador` que audita negações (UC04 Exceção I) | `src/core/application/seguranca/*` |
| 2.4 | UC01/UC04: `RegistrarOcorrencia`, `Consultar`, `Validar`, `Devolver`, `Corrigir` | `src/core/application/usecases/OcorrenciaUseCases.ts` |
| 2.5 | UC02: `AtualizarTelemetria`, `ConsultarViaturas`, `SugerirViaturasProximas`, `DespacharViatura`, `ConsultarDespachos` | `src/core/application/usecases/DespachoUseCases.ts` |
| 2.6 | `AutenticarUsuario`, `ConsultarAuditoria` | `src/core/application/usecases/SegurancaUseCases.ts` |
| 2.7 | Eventos de domínio (`ocorrencia.alterada`, `viatura.posicao`, `viatura.despachada`) | `src/core/application/usecases/Eventos.ts` |

**Verificação:** `tests/usecases/*.test.ts` (30 testes) cobrindo todos os critérios de aceite da Seção 3.4 e os cenários de exceção dos UC01/UC02/UC04.

## Fase 3 — Adaptadores de saída ✅

| Passo | Ação | Arquivo(s) |
| :-: | :--- | :--- |
| 3.1 | Repositórios em memória (snapshot + reidratação — mesmo padrão de um adaptador de banco) | `src/adapters/outbound/persistencia/memoria/*` |
| 3.2 | Auditoria hash-chain com fila serializada (sem bifurcação sob concorrência) e `verificarIntegridade` | `src/adapters/outbound/auditoria/AuditoriaHashChain.ts` |
| 3.3 | Barramento de eventos em processo (isola assinantes com defeito) | `src/adapters/outbound/eventos/*` |
| 3.4 | `RelogioSistema`, `GeradorIdCrypto`, `HashNodeCrypto` | `src/adapters/outbound/infra/*`, `.../seguranca/*` |
| 3.5 | Seed: 6 usuários (todos os papéis) e 6 viaturas em Alegrete/RS | `src/config/seed.ts` |

## Fase 4 — Adaptadores de entrada ✅

| Passo | Ação | Arquivo(s) |
| :-: | :--- | :--- |
| 4.1 | Sessão em cookie HMAC-SHA256 `httpOnly` (8 h), sem lib JWT | `src/adapters/inbound/next/sessao.ts` |
| 4.2 | Tradução de erros de domínio → HTTP (422/404/409/403/412) e Zod → 400 | `src/adapters/inbound/http/respostas.ts` |
| 4.3 | Esquemas Zod (validação sintática; a semântica fica no domínio) | `src/adapters/inbound/http/esquemas.ts` |
| 4.4 | Route Handlers REST em `app/api/**` (ver [04](04-arquitetura-implementada.md#api)) | `app/api/**/route.ts` |
| 4.5 | SSE `/api/eventos` com heartbeat e limpeza no `abort` (P03) | `src/adapters/inbound/sse/fluxoEventos.ts` |
| 4.6 | Simulador GPS (driver) com falha intermitente na `vtr-05` para exercitar RNF04 | `src/adapters/inbound/simulador-gps/SimuladorGps.ts` |
| 4.7 | *Composition root* único com singleton em `globalThis` (P06) e *bootstrap* via `instrumentation.ts` | `src/config/container.ts`, `instrumentation.ts` |

## Fase 5 — Interface React ✅

| Passo | Tela | Arquivo(s) | Requisito |
| :-: | :--- | :--- | :--- |
| 5.1 | Login com contas de demonstração | `app/login/page.tsx` | RNF02 |
| 5.2 | Layout autenticado com menu por papel | `app/(app)/layout.tsx` | RNF02 |
| 5.3 | Lista de ocorrências (Agente vê só as suas) | `app/(app)/ocorrencias/page.tsx` | RF01 |
| 5.4 | Formulário de registro (fato, local, envolvidos dinâmicos, evidências com rejeição de formato) | `app/_componentes/FormularioOcorrencia.tsx` | UC01 |
| 5.5 | Detalhe da ocorrência + ações por papel (validar/devolver/corrigir) | `app/(app)/ocorrencias/[id]/page.tsx`, `AcoesOcorrencia.tsx` | UC04 |
| 5.6 | Fila de revisão do Delegado | `app/(app)/revisao/page.tsx` | UC04 |
| 5.7 | Painel tático: Leaflet + SSE + sugestões + despacho + fallback tabular + despacho manual | `PainelTatico.tsx`, `MapaTatico.tsx` | UC02, RNF01, RNF04 |
| 5.8 | Log de auditoria com verificação de integridade | `app/(app)/auditoria/page.tsx` | RNF03 |
| 5.9 | Fronteira de erro (`error.tsx`) | `app/(app)/error.tsx` | RNF04 |

## Fase 6 — Verificação ✅

| Passo | Ação | Resultado obtido |
| :-: | :--- | :--- |
| 6.1 | `npm test` | 46 testes, 5 arquivos, ~200 ms |
| 6.2 | `npm run typecheck` + `npm run build` | Sem erros; 22 rotas |
| 6.3 | Smoke E2E via `curl` em `next start` e `next dev` | Login → registro → 403 p/ agente validar → validação com hash → 3 sugestões ordenadas → despacho → status corretos → auditoria íntegra (8 registros) → SSE emitindo |
| 6.4 | Verificação visual do mapa no navegador | **Não executada nesta iteração** (sem navegador no ambiente). O build compila `MapaTatico` sem erros; a validação visual é o primeiro item da Fase 7. |

---

## Fase 7 — Próximos passos (ordem recomendada) 🔜

1. **Validar o painel no navegador** (Chrome/Firefox): marcadores, tooltip, seleção por clique, fallback ao bloquear `tile.openstreetmap.org` no DevTools.
2. **Escolher e implementar persistência real** — decisão pendente da equipe (P01/P08). Recomendação: **PostgreSQL + Prisma** (transações para o despacho e contador de protocolo; `auditoria` como tabela *append-only* com trigger que proíbe UPDATE/DELETE). Alternativa Firestore: usar `runTransaction` e contadores distribuídos.
   - Implementar `RepositorioOcorrenciasPostgres` etc. cumprindo as portas de `src/core/application/ports/outbound/Repositorios.ts`; trocar em `container.ts`. **Nenhuma linha de `src/core` muda.**
   - Introduzir uma porta `UnidadeDeTrabalho` para tornar `DespacharViatura` atômico (P07).
3. **Testes E2E com Playwright** do roteiro do [README](README.md#roteiro-de-demonstração) (substitui o Selenium previsto — P12).
4. **Armazenamento de evidências** (Firebase Storage/S3) com hash do binário real e limite de tamanho; manter a porta `PortaHash`.
5. **Lint de fronteiras** (`eslint-plugin-boundaries` ou `dependency-cruiser`) para impedir importações de framework em `src/core`.
6. **Deploy** (Docker + `next start`, `SESSION_SECRET` obrigatório, `GPS_SIMULADOR_ATIVO=false` em produção quando houver telemetria real via `POST /api/viaturas/:id/telemetria`).
7. **Should Have** na ordem RF03 → RF07 → RF05 (ver estimativas em [01](01-analise-de-complexidade.md#4-esforço-estimado-ordem-de-grandeza-para-o-restante)).

## Fase 8 — Ciclos futuros ⏳

- Provedor de identidade (OIDC/LDAP) substituindo o seed de usuários; MFA para Delegado.
- Redis Pub/Sub como `PublicadorEventos` para escala horizontal do SSE.
- Assinatura digital (ICP-Brasil) do ato de validação e dos laudos; carimbo de tempo.
- Reforço de viaturas (despacho múltiplo — UC02 Alt. I) exige permitir despacho em `EM_ATENDIMENTO` (P16).
- Criptografia de PII (CPF) em repouso e mascaramento em logs (P13).

---

## Comandos de referência

```bash
npm run dev          # desenvolvimento (Turbopack, HMR)
npm test             # núcleo hexagonal
npm run typecheck    # tsc --noEmit
npm run build        # build de produção
SESSION_SECRET=... npm start
```

Telemetria externa (simula hardware GPS):
```bash
curl -X POST localhost:3000/api/viaturas/vtr-01/telemetria \
  -H 'Content-Type: application/json' -H 'x-telemetria-token: token-telemetria-dev' \
  -d '{"coordenada":{"latitude":-29.78,"longitude":-55.79}}'
```
