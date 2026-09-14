# ETAPA 07 — Frontend do MVP (login, registro, fila do Delegado, correção, painel tático)

**Data:** 13/09/2026 · **Prioridade:** 🔴 (Verificações 2 e 3 são demonstradas pela UI)

**Origem:** `ETAPA-04` RF01\*, RF04\*, RF11, RF13, RF14, RF15, RF16, RF17 (cliente), RF18, RF19, RNF04\*, RNF08, RNF12; `ETAPA-05` NEXT-06/07/08/09/11/13/14 (parte de UI); HEX-14; DIV-30.

## 1. Objetivo

Dar ao MVP a interface por papel que o §3.3 da Documentação de Engenharia descreve: Agente registra (com coordenada), Delegado revisa, Operador vê a frota em tempo real no mapa, recebe sugestões e despacha.

## 2. O que foi implementado

| Item | Arquivo | Requisito |
| :--- | :--- | :--- |
| Tipos espelhando o OpenAPI (`Papel`, `StatusOcorrencia`, `Viatura`, `Sugestoes`, `OrdemDespacho`, `EventoTempoReal`, `ErroApi`…) — substitui `types/ocorrencia.ts` (DIV-30) | `src/types/api.ts` | RNF12 |
| Cliente axios com **Bearer do token**, `Accept-Language`, 401 → sessão expirada; `mensagemDeErro()` mostra o `detail` i18n do backend + `request_id` curto | `src/services/api.ts` | RF11, RNF08, RNF09 |
| Sessão em `sessionStorage` com expiração local (8 h) | `src/services/sessao.ts` | RNF02\* |
| Serviços `auth`, `ocorrencias` (listar/detalhe/validar/devolver/rejeitar/corrigir/reenviar/encerrar), `viaturas` (+ simulador), `despacho` | `src/services/*.ts` | RF13, RF04\*, RF14, RF15, RF16, RF18, RF19 |
| **`ClienteTempoReal`**: WebSocket com *backoff* 1/2/4/8/16/30 s, *keep-alive*, recarga por REST ao reconectar, não reconecta em 1008 (token inválido) | `src/services/tempoRealService.ts` | RF17 aceite 2, RNF04\* |
| `AuthProvider`/`useAuth` (`tem(...papeis)`), `ToastProvider` (substitui `alert()`), `useTempoReal` | `src/hooks/` | — |
| `AppShell` com navegação **por papel** e seletor PT/EN; `RequireRole` (rota protegida + redireciona por papel) | `src/components/layout/AppShell.tsx`, `src/components/RequireRole.tsx` | RF12, RNF08 |
| `LoginPage` | `src/pages/LoginPage.tsx` | RF11 |
| `OcorrenciaForm` reutilizável (registro e correção) com **`SeletorCoordenada`** (mapa Leaflet clicável/arrastável + campos numéricos), `data_hora_fato` (não futura), validação local espelhando o domínio (descrição ≥ 20, ≥ 1 envolvido) | `src/components/ocorrencias/OcorrenciaForm.tsx`, `src/components/painel/SeletorCoordenada.tsx` | RF01\*, DEC-03 |
| `RegistrarOcorrenciaPage` (sem `agente_policial_id` fixo — HEX-14) | `src/pages/RegistrarOcorrenciaPage.tsx` | RF01\* |
| `MinhasOcorrenciasPage`: lista do agente, detalhe, **edição + reenvio** das devolvidas com a justificativa do Delegado visível | `src/pages/MinhasOcorrenciasPage.tsx` | RF14 |
| `OcorrenciaDetalheView`: envolvidos, tipificações, histórico de status, indicador de integridade SHA-256, justificativa/desfecho | `src/components/ocorrencias/OcorrenciaDetalhe.tsx` | RF13, DEC-09 |
| `FilaDelegadoPage`: 4 filtros de status, fila mais antiga primeiro, detalhe e decisões **validar / devolver / rejeitar** (justificativa ≥ 10, confirmação na rejeição) | `src/pages/FilaDelegadoPage.tsx` | RF04\*, RF13 |
| **`PainelTaticoPage`**: mapa Leaflet/OSM com marcadores incrementais (viaturas coloridas por situação/sinal, ocorrências validadas), indicador de conexão, **liga/desliga simulador**, lista de validadas, **sugestão das 3 mais próximas com distância + botão despachar**, despacho manual quando não há elegíveis, encerramento com desfecho, tabela da frota, **alerta + tabela de última posição para viaturas sem sinal** (recalculado no cliente a cada 5 s) | `src/pages/PainelTaticoPage.tsx`, `src/components/painel/MapaTatico.tsx`, `src/components/painel/leaflet.ts` | RF16, RF17, RF18, RF19, RNF04\*, critérios 3–5 do MVP |
| `FrotaPage`: cadastro e situação manual | `src/pages/FrotaPage.tsx` | RF15 |
| Rotas com `react-router-dom` 6 (`/login`, `/registrar`, `/minhas`, `/fila`, `/painel`, `/frota`) | `src/App.tsx` | — |
| i18n em 4 *namespaces* (`common`, `auth`, `ocorrencias`, `painel`) em `pt` e `en`; idioma persistido | `public/locales/*` | RNF08 |
| Estilos próprios (sem framework), responsivo até ~900 px | `src/styles.css` | — |
| Proxy Vite para `/v1` **com WebSocket** e `/health` | `vite.config.ts` | — |

## 3. Decisões tomadas durante a implementação

- **Token em `sessionStorage`** (não `localStorage`): morre com a aba, alinhado ao turno de 8 h. XSS/CSP ficam para a revisão de segurança prevista na Sprint 5 (E8 da análise).
- O mapa é atualizado **incrementalmente** (marcadores reaproveitados) para suportar 1 Hz × N viaturas sem recriar a camada.
- Eventos WS atualizam o estado local; `OcorrenciaValidada` recarrega a lista por REST (o evento traz só id/coordenada). Ao reconectar, tudo é recarregado (RF17: "carga inicial por REST").
- O indicador `SEM_SINAL` é recalculado no cliente (idade > 60 s) porque o backend só reavalia ao servir uma requisição.
- Coordenada padrão do mapa = Alegrete/RS, mesmo centro do simulador.
- Sem dependência de UI (Tailwind/MUI) para manter o *bundle* pequeno (152 kB gzip) e a build simples.

## 4. Verificação

| Verificação | Resultado |
| :--- | :--- |
| `npx tsc --noEmit` (strict, `noUnusedLocals`) | OK |
| `npx vite build` | OK — 146 módulos, 474 kB (152 kB gzip) |
| **Smoke test ao vivo**: backend `uvicorn` com SQLite migrado (`alembic upgrade head` + `scripts.seed`) + `vite` dev; fluxo executado **através do proxy do Vite** (`localhost:3001/v1/...`) | login dos 3 papéis → `SGOPI-2026-000001` registrado → validado → simulador ligado (4 ticks, 20 posições) → sugestões `[VTR-03 0,92 km, VTR-04 1,38 km, VTR-02 1,48 km]` → `OD-2026-000001` → `ENCERRADA` com histórico de 4 estados → auditoria com 7 registros; **0 erros** no log do servidor |
| Suíte backend | 176 passed (inalterada) |

**Não verificado nesta etapa:** renderização em navegador real (não há navegador/Playwright neste ambiente). Os testes E2E com Selenium continuam previstos para a Sprint 5 (F1/F2; E10 da análise).

## 5. Fora desta etapa

- Notificação in-app (RF21) e evidências (RF22) — *Should*.
- Testes E2E de navegador, revisão de segurança do frontend (E8), medição de latência p95 (E9).

## 6. Rastreabilidade

HEX-14 ✅ · DIV-30 ✅ · RF17 ✅ (cliente com reconexão) · RNF04\* ✅ (fallback tabular e reconexão) · RNF08 ✅ · critérios de aceite do MVP §3.4: 1 ✅ 2 ✅ 3 ✅ (entrega sem *refresh*; latência a medir) 4 ✅ 5 ✅
