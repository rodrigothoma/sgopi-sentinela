# 04 — Arquitetura Implementada

Mapa do código para a Arquitetura Hexagonal descrita na Seção 4 da especificação, mais os contratos que a equipe precisa conhecer para evoluir o MVP.

## 1. Estrutura de pastas

```
sgopi-sentinela/
├── app/                              # Next.js App Router — ADAPTADOR de entrada (UI React + REST + SSE)
│   ├── api/**/route.ts               #   Route Handlers (REST)  → chamam casos de uso via container
│   ├── (app)/                        #   páginas autenticadas (Server Components leem casos de uso)
│   ├── login/                        #   página pública
│   ├── _componentes/                 #   Client Components (formulário, painel, mapa, ações)
│   └── _lib/                         #   cliente HTTP, navegação, formatação
├── src/
│   ├── core/                         # NÚCLEO — sem importações de framework
│   │   ├── domain/                   #   entidades, objetos de valor, regras puras
│   │   │   ├── shared/               #     DomainError, Coordenada (Haversine), Evento
│   │   │   ├── ocorrencia/           #     Ocorrencia (agregado), Envolvido, EvidenciaDigital, StatusOcorrencia
│   │   │   ├── viatura/              #     Viatura (GPS 60 s, despacho)
│   │   │   ├── despacho/             #     OrdemDespacho
│   │   │   ├── auditoria/            #     RegistroAuditoria (hash-chain)
│   │   │   └── usuario/              #     Papel (RBAC), Usuario
│   │   └── application/
│   │       ├── ports/inbound/        #   contratos dos casos de uso (o que o mundo pode pedir)
│   │       ├── ports/outbound/       #   contratos de infraestrutura (o que o núcleo precisa)
│   │       ├── seguranca/            #   Ator, matriz RBAC, Autorizador
│   │       └── usecases/             #   implementações dos casos de uso + eventos
│   ├── adapters/
│   │   ├── inbound/                  # ADAPTADORES de entrada
│   │   │   ├── http/                 #   Zod, tradução de erros → HTTP, wrapper comAtor
│   │   │   ├── next/                 #   sessão (cookie HMAC)
│   │   │   ├── sse/                  #   fluxo Server-Sent Events
│   │   │   └── simulador-gps/        #   driver que substitui o hardware GPS
│   │   └── outbound/                 # ADAPTADORES de saída
│   │       ├── persistencia/memoria/ #   repositórios em memória
│   │       ├── auditoria/            #   AuditoriaHashChain
│   │       ├── eventos/              #   barramento em processo
│   │       ├── infra/                #   relógio, ids
│   │       └── seguranca/            #   SHA-256 (node:crypto)
│   └── config/
│       ├── container.ts              # COMPOSITION ROOT (único lugar que liga portas a adaptadores)
│       └── seed.ts                   # usuários e viaturas de demonstração
├── instrumentation.ts                # bootstrap do container ao subir o servidor
├── tests/                            # vitest — só o núcleo + adaptadores puros (sem Next/DB)
└── docs/mvp/                         # esta documentação
```

### Regra de dependência (verificável)

```bash
grep -rE 'from "(next|react|zod|leaflet|node:)' src/core   # deve retornar vazio
```

| Camada | Pode importar | Não pode importar |
| :--- | :--- | :--- |
| `src/core/domain` | nada externo | tudo o mais |
| `src/core/application` | `domain` | adaptadores, frameworks |
| `src/adapters/*` | `core` (portas e tipos) | outros adaptadores (exceto via portas) |
| `src/config` | tudo | — (é o único que conhece implementações concretas) |
| `app/*` | `config` (container), `adapters/inbound`, tipos do `core` | adaptadores de saída diretamente |

## 2. Diagrama de componentes (como implementado)

```
        ┌──────────────────────── ADAPTADORES DE ENTRADA ────────────────────────┐
        │  React (app/**)   REST (app/api/**)   SSE (/api/eventos)   SimuladorGps │
        └─────────────┬────────────┬──────────────────┬──────────────────┬────────┘
                      ▼            ▼                  │ assina           ▼
        ┌──────────────── PORTAS DE ENTRADA (ports/inbound/CasosDeUso.ts) ─────────┐
        │ RegistrarOcorrencia · ValidarOcorrencia · DevolverOcorrenciaParaCorrecao │
        │ CorrigirOcorrencia · ConsultarOcorrencias · AtualizarTelemetriaViatura    │
        │ SugerirViaturasProximas · DespacharViatura · ConsultarViaturas/Despachos │
        │ AutenticarUsuario · ConsultarAuditoria                                    │
        └──────────────────────────────────┬────────────────────────────────────────┘
                                           ▼
        ┌──────────────────────────── NÚCLEO ───────────────────────────────────────┐
        │  usecases/*  ──usa──▶  seguranca/Autorizador (RBAC + auditoria de negação) │
        │      │                                                                     │
        │      ▼                                                                     │
        │  domain: Ocorrencia · Viatura · OrdemDespacho · RegistroAuditoria · Papel  │
        └──────────────────────────────────┬────────────────────────────────────────┘
                                           ▼
        ┌──────────────── PORTAS DE SAÍDA (ports/outbound/*.ts) ───────────────────┐
        │ RepositorioOcorrencias · RepositorioViaturas · RepositorioDespachos       │
        │ RepositorioUsuarios · PortaAuditoria · PublicadorEventos                  │
        │ PortaRelogio · PortaGeradorId · PortaHash                                 │
        └─────────────┬──────────────┬───────────────┬──────────────┬──────────────┘
                      ▼              ▼               ▼              ▼
        ┌──────────────────────── ADAPTADORES DE SAÍDA ───────────────────────────┐
        │ Repositórios em memória │ AuditoriaHashChain │ Barramento em processo │  │
        │ RelogioSistema · GeradorIdCrypto · HashNodeCrypto                        │
        └──────────────────────────────────────────────────────────────────────────┘
```

## 3. Máquina de estados da ocorrência

```
                 devolverParaCorrecao (DELEGADO, justificativa ≥ 10)
        ┌────────────────────────────────────────────────────────┐
        ▼                                                        │
  EM_CORRECAO ──corrigirEReenviar (AGENTE autor)──▶ AGUARDANDO_REVISAO ──validar (DELEGADO, despacho)──▶ VALIDADA
                                                                                                          │
                                                       iniciarAtendimento (via DespacharViatura, OPERADOR) │
                                                                                                          ▼
                                                                                   EM_ATENDIMENTO ──concluir──▶ CONCLUIDA
```
Toda transição é registrada em `historico[]` (de, para, em, autorId, motivo). Após `validar`, `hashIntegridade` bloqueia `corrigirEReenviar`.

Viatura: `DISPONIVEL ──despachar──▶ EM_DESLOCAMENTO ──chegarAoLocal──▶ EM_ATENDIMENTO ──liberar──▶ DISPONIVEL`; `INDISPONIVEL` nunca recebe despacho nem telemetria do simulador.

## 4. Matriz RBAC (RNF02) — `src/core/application/seguranca/PoliticaAutorizacao.ts`

| Ação | AGENTE | DELEGADO | OPERADOR_CENTRAL | SUPERVISOR | PERITO |
| :--- | :-: | :-: | :-: | :-: | :-: |
| ocorrencia.registrar | ✓ | | | | |
| ocorrencia.corrigir | ✓ (autor) | | | | |
| ocorrencia.consultar | ✓ (próprias) | ✓ | ✓ | ✓ | ✓ |
| ocorrencia.validar / devolver | | ✓ | | | |
| viatura.consultar | | ✓ | ✓ | ✓ | |
| viatura.telemetria | | | | ✓ (ator SISTEMA) | |
| despacho.sugerir | | | ✓ | ✓ | |
| despacho.emitir | | | ✓ | | |
| auditoria.consultar | | ✓ | | ✓ | |

Negações lançam `ErroNaoAutorizado` (HTTP 403) **e** gravam registro `NEGADO` com `alertaSeguranca: true` na auditoria (UC04 Exceção I).

## 5. API

Todas as rotas (exceto login e telemetria) exigem o cookie `sgopi_sessao`. Erros seguem `{ erro: { codigo, mensagem, detalhes } }`.

| Método | Rota | Caso de uso | Sucesso | Erros típicos |
| :-- | :-- | :-- | :-: | :-- |
| POST | `/api/auth/login` `{matricula, senha}` | AutenticarUsuario | 200 `{ator}` | 403 |
| POST | `/api/auth/logout` | — | 200 | |
| GET | `/api/auth/sessao` | — | 200/401 | |
| GET | `/api/ocorrencias?status=A,B` | ConsultarOcorrencias.listar | 200 `{ocorrencias}` | 401/403 |
| POST | `/api/ocorrencias` | RegistrarOcorrencia (UC01) | 201 `{ocorrencia}` | 400 (Zod) · 422 (domínio) · 403 |
| GET | `/api/ocorrencias/:id` | ConsultarOcorrencias.obter | 200 | 404 |
| POST | `/api/ocorrencias/:id/validar` `{despachoAutoridade}` | ValidarOcorrencia (UC04) | 200 | 403 · 409 (transição) · 422 |
| POST | `/api/ocorrencias/:id/devolver` `{pendencias}` | DevolverOcorrenciaParaCorrecao | 200 | 403 · 409 · 422 |
| POST | `/api/ocorrencias/:id/corrigir` `{descricaoFato}` | CorrigirOcorrencia | 200 | 403 · 409 · 412 |
| GET | `/api/viaturas` | ConsultarViaturas | 200 `{viaturas[].sinalGpsValido}` | 403 |
| POST | `/api/viaturas/:id/telemetria` (header `x-telemetria-token`) | AtualizarTelemetriaViatura | 202 | 401 · 404 |
| GET | `/api/despachos/sugestoes?ocorrenciaId=` | SugerirViaturasProximas (UC02 p.4) | 200 `{sugestoes[], despachoAutomaticoBloqueado}` | 412 (não validada) |
| POST | `/api/despachos` `{ocorrenciaId, viaturaId, posicaoInformada?}` | DespacharViatura (UC02) | 201 `{ordem}` | 412 (GPS/indisponível/não validada) · 403 |
| GET | `/api/despachos` | ConsultarDespachos | 200 | 403 |
| GET | `/api/auditoria?limite=` | ConsultarAuditoria | 200 `{registros, integra}` | 403 |
| GET | `/api/eventos` | (SSE) assina PublicadorEventos | `text/event-stream` | 401/403 |

### Eventos SSE

| `event:` | `data` | Origem |
| :-- | :-- | :-- |
| `conectado` | `{em}` | abertura do fluxo |
| `viatura.posicao` | `{viaturaId, prefixo, status, coordenada, recebidaEm}` | AtualizarTelemetria (simulador ou hardware) |
| `ocorrencia.alterada` | `{ocorrenciaId, protocolo, status, gravidade, coordenada?}` | registrar/validar/devolver/corrigir/despachar |
| `viatura.despachada` | `{viaturaId, prefixo, ocorrenciaId, protocolo, ordemId}` | DespacharViatura |
| `: ping` | — | heartbeat a cada 15 s |

## 6. Auditoria (RNF03)

Cada registro: `{sequencia, registradoEm, atorId, atorPapel, acao, recursoTipo, recursoId, resultado, detalhes?, hashAnterior, hash}` com `hash = SHA-256(canônico(registro sem hash))` e `hashAnterior = hash do registro anterior` (gênese = 64 zeros). `verificarIntegridade()` percorre a cadeia e aponta a primeira sequência corrompida (testado com adulteração simulada). Gravações são serializadas por uma fila de promessas para nunca bifurcar sob concorrência.

Operações auditadas: `auth.login` (sucesso/negado), `ocorrencia.registrar|validar|devolver|corrigir`, `despacho.emitir`, e **toda** negação RBAC. Telemetria não é auditada individualmente (volume).

## 7. Variáveis de ambiente

| Variável | Padrão | Uso |
| :-- | :-- | :-- |
| `SESSION_SECRET` | *(obrigatória em produção)* | HMAC do cookie de sessão |
| `TELEMETRIA_TOKEN` | `token-telemetria-dev` | `POST /api/viaturas/:id/telemetria` |
| `GPS_SIMULADOR_ATIVO` | `true` | desligar quando houver telemetria real |
| `GPS_SIMULADOR_INTERVALO_MS` | `2000` | cadência do simulador |

## 8. Como trocar um adaptador (exemplo: PostgreSQL)

1. Criar `src/adapters/outbound/persistencia/postgres/RepositorioOcorrenciasPostgres.ts` implementando `RepositorioOcorrencias` (usar `Ocorrencia.paraEstado()` para gravar e `Ocorrencia.reidratar()` para ler).
2. Em `src/config/container.ts`, substituir `new RepositorioOcorrenciasEmMemoria()` pela nova classe.
3. Rodar `npm test` — os testes do núcleo continuam usando os adaptadores em memória e **não devem mudar**.
4. Adicionar testes de integração do adaptador (com banco) em uma pasta separada (`tests/integracao`), fora da suíte rápida.
