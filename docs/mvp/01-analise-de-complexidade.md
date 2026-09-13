# 01 — Análise de Complexidade

## 1. Complexidade do prompt de implementação

O pedido que originou este trabalho foi: *"analise o arquivo `DOCUMENTAÇÃO_DE_ENGENHARIA.MD` e implemente os requisitos funcionais e não funcionais mais críticos seguindo a arquitetura hexagonal; o projeto deverá utilizar React para o front-end e Next.js para o backend; analise a complexidade dos requisitos e do prompt; gere documentação em `/docs` com os passos para criar um MVP e os problemas encontrados que não foram descobertos anteriormente"*.

### 1.1 Decomposição

| # | Sub-tarefa | Natureza | Dificuldade |
| :-: | :--- | :--- | :-: |
| 1 | Ler e interpretar ~750 linhas de especificação (10 RF, 5 RNF, 12 UC, MoSCoW, MVP) | Análise | Média |
| 2 | Selecionar "os mais críticos" | Decisão | Baixa — a matriz MoSCoW já define *Must Have* = RF01, RF04, RF02 |
| 3 | Projetar núcleo hexagonal em TypeScript (domínio, casos de uso, portas) | Projeto | Alta |
| 4 | Implementar adaptadores (HTTP, SSE, simulador GPS, persistência, auditoria, sessão) | Implementação | Alta |
| 5 | Implementar UI React (5 telas + mapa em tempo real) | Implementação | Média-Alta |
| 6 | Testar (unidade do núcleo + smoke E2E) | Verificação | Média |
| 7 | Documentar complexidade, passos e problemas | Escrita | Média |

### 1.2 Ambiguidades do prompt e decisões tomadas

| Ambiguidade | Leituras possíveis | Decisão | Justificativa |
| :--- | :--- | :--- | :--- |
| "React para o front-end e Next.js para o backend" | (a) dois projetos — SPA React (Vite) + API Next; (b) um projeto Next.js usando React no App Router e Route Handlers como backend | **(b)** | Menos infraestrutura para a equipe (1 processo, 1 `package.json`, sem CORS). A separação hexagonal continua rigorosa: `src/core` não importa nada de `next`/`react`. Se no futuro for preciso separar, `src/core` + `src/adapters/outbound` migram para um serviço Node sem alteração. |
| Contradição com a especificação (Python/FastAPI + Firestore na Seção 4.3; PostgreSQL no README) | Seguir o doc ou o prompt | **Prompt** | Instrução explícita e mais recente do solicitante. A divergência está registrada em [03 — Problemas](03-problemas-encontrados.md#p01). |
| "Mais críticos" | Só os *Must Have*; ou *Must* + RNFs | **Must Have + todos os RNFs** | RNF01–RNF05 são transversais e não podem ser adicionados depois sem retrabalho (auditoria, RBAC, fallback de GPS, desacoplamento). |
| Persistência | Banco real vs. memória | **Memória atrás de portas** | Nenhum SGBD está provisionado; um adaptador em memória entrega o fluxo completo e permite trocar por Firestore/PostgreSQL alterando apenas `src/config/container.ts`. Custo: dados voláteis (ver P09). |
| "Tempo real via WebSockets" | WebSocket puro vs. alternativa | **SSE** | Next.js não expõe o servidor HTTP para *upgrade* WS em Route Handlers (P03). |

### 1.3 Classificação global

**Complexidade do prompt: alta.** Combina análise de requisitos, decisão arquitetural sob contradição de fontes, implementação *full-stack* com tempo real, e produção documental. O maior risco não era técnico, mas de **escopo**: sem a matriz MoSCoW já existente, "mais críticos" seria indefinido.

---

## 2. Complexidade dos requisitos funcionais

Escala: **B**aixa · **M**édia · **A**lta · **MA** Muito alta. "Domínio" = regras de negócio; "Integração" = dependências externas; "UI" = interface.

| RF | MoSCoW | Domínio | Integração | UI | Global | Observações |
| :-- | :-- | :-: | :-: | :-: | :-: | :--- |
| RF01 Ocorrência | Must | M | B (M com upload real) | M | **M** | Agregado com envolvidos/evidências, validações, protocolo único. Upload binário real (storage + antivírus) eleva para A. |
| RF04 Aprovação | Must | M | B | B | **M** | Máquina de estados + RBAC estrito + selo de integridade. Assinatura ICP-Brasil (fora do MVP) elevaria para A. |
| RF02 Despacho | Must | M | A | A | **A** | Telemetria contínua, tolerância de 60 s, Haversine, fallback manual, mapa em tempo real. Hardware GPS real e roteamento por vias (em vez de linha reta) elevariam para MA. |
| RF03 Apreensões | Should | M | B | M | **M** | Cadeia de custódia = log imutável por item; unicidade de lacre. Reaproveita a auditoria hash-chain já implementada. |
| RF05 Manchas criminais | Should | A | M | A | **A** | KDE/heatmap, janelas temporais, comparação de períodos, gatilhos (UC11). Exige volume histórico e *jobs* agendados. |
| RF07 Laudos | Should | M | A | M | **A** | Validação de assinatura digital (ICP-Brasil) é integração pesada; imutabilidade + aditamentos. |
| RF06 Inquéritos | Could | A | B | M | **A** | "Sugerir conexões automáticas" (CPF, apelido, placa, geolocalização) é um problema de *record linkage*. |
| RF08 Autenticação pública | Could | B | M (QR/PDF) | B | **M** | Simples se RNF03 já produz hash de documento; exige mascaramento LGPD (RNF02). |
| RF09 Medidas protetivas | Could | M | B | M | **M** | Prazos + *scheduler* (UC12) + detecção de reincidência cruzando envolvidos. |
| RF10 Interagências | Won't | M | A | M | **A** | Mensageria assíncrona com retentativas, níveis de sigilo, entrega garantida. |

## 3. Complexidade dos requisitos não funcionais

| RNF | Complexidade | Como foi atendido no MVP | O que ainda pesa |
| :-- | :-: | :--- | :--- |
| RNF01 Tempo real | **A** | SSE (`/api/eventos`) + barramento em processo; simulador a cada 2 s; painel atualiza sem *refresh*; latência medida < 100 ms local. | Múltiplas instâncias exigem Redis Pub/Sub; proxies precisam desabilitar *buffering*. |
| RNF02 RBAC | **M** | Matriz `MATRIZ_PERMISSOES` aplicada nos casos de uso (defesa em profundidade) e nas páginas; sessão HMAC assinada; tentativas negadas auditadas. | Provedor de identidade real (LDAP/OIDC), MFA, revogação de sessão, mascaramento de PII no portal público (RF08). |
| RNF03 Imutabilidade/Auditoria | **A** | Log *append-only* com hash-chain SHA-256 verificável; narrativa selada por hash na validação; ordens de despacho congeladas; retificações geram registros com hash anterior/novo. | Persistência *write-once* real (tabela sem UPDATE/DELETE, WORM), carimbo de tempo confiável, assinatura digital. |
| RNF04 Resiliência | **M** | GPS > 60 s ⇒ bloqueio do automático + despacho manual com posição via rádio; falha de tiles ⇒ listagem tabular; simulador tolera erros por *tick*; barramento isola assinantes com defeito. | Retentativas com *backoff* em integrações externas reais; *circuit breaker*; fila durável para eventos perdidos durante reconexão SSE. |
| RNF05 Desacoplamento | **M** | `src/core` sem importações de framework (verificável por `grep`); *composition root* único; testes do núcleo rodam sem Next/DB em ~200 ms. | Manter disciplina (lint de fronteiras, ex. `eslint-plugin-boundaries`). |

## 4. Esforço estimado (ordem de grandeza) para o restante

| Item | Estimativa (pessoa-dias) | Pré-requisito |
| :--- | :-: | :--- |
| Adaptador de persistência real (PostgreSQL/Prisma **ou** Firestore) + migração de seed | 3–5 | Decisão de SGBD (ver P01/P08) |
| Armazenamento de evidências (S3/Firebase Storage) + hash real do binário | 2–3 | Persistência |
| RF03 Apreensões | 3–4 | Persistência |
| RF07 Laudos (sem ICP-Brasil real: validação de hash + assinatura institucional) | 4–6 | RF03 |
| RF05 Manchas criminais (heatmap Leaflet + agregação por janela) | 5–8 | Volume de dados / seed sintético |
| Testes E2E (Playwright) do fluxo do MVP | 2–3 | — |
| Redis Pub/Sub para SSE multi-instância | 1–2 | Deploy com > 1 réplica |
