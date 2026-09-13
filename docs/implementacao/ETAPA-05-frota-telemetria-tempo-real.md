# ETAPA 05 — Frota, telemetria com simulador e canal de tempo real (RF15, RF16, RF17)

**Data:** 13/09/2026 · **Branch:** `matheus-Fastapi` · **Prioridade:** 🔴 (Must Have — Sprint 4 / critérios de aceite 3 e 4 do MVP)
**Origem:** `ETAPA-04` §2 (máquina de estados da viatura), §4 (RF15, RF16, RF17), §5 (RNF01\*, RNF04\*), DEC-06; `ETAPA-05` NEXT-11, NEXT-12, NEXT-13; RF-P08, RF-P12, RNF-P02, RNF-P13, RNF-P15.

## 1. Objetivo

Desmembrar o "requisito-iceberg" RF02 nas suas três primeiras capacidades: cadastro de viaturas, ingestão de posições (com simulador como *driving adapter*) e canal WebSocket que leva eventos ao painel sem *refresh*.

## 2. O que foi implementado

| Item | Arquivo | Requisito |
| :--- | :--- | :--- |
| Entidade `Viatura` + `SituacaoViatura` (`DISPONIVEL ⇄ INDISPONIVEL`, `DISPONIVEL → EM_DESLOCAMENTO → OPERANDO → DISPONIVEL`), VO `Posicao`, `registrar_posicao` com janela de ±60 s e rejeição de posição retroativa (posição anterior mantida), `sinal()` = `OK / SEM_SINAL / SEM_POSICAO` | `domain/viatura/entity.py` | RF15, RF16, RNF04\*, RNF-P15 |
| Eventos `PosicaoAtualizada`, `ViaturaSituacaoAlterada` | `domain/viatura/eventos.py` | RF17 |
| Porta `RepositorioViatura`; portas de entrada `InterfaceCadastrarViatura`, `InterfaceAlterarSituacaoViatura`, `InterfaceListarViaturas`, `InterfaceRegistrarPosicaoViatura` | `application/ports/` | RF15, RF16 |
| Casos de uso `CadastrarViatura` (prefixo/placa únicos → 409), `AlterarSituacaoViatura` (só `DISPONIVEL`/`INDISPONIVEL` manual; despachada não pode ser retirada), `ListarViaturas`, `RegistrarPosicaoViatura` (sem auditoria por volume; publica evento após commit) | `application/use_cases/viatura/` | RF15 aceites 1–2, RF16 aceite 1/3 |
| `ViaturaModel` + migration `0002_viaturas` (validada com `alembic check`); `ViaturaRepositorioSQLAlchemy` com optimistic locking | `infrastructure/database/`, `adapters/outbound/persistence/viatura_repositorio_sqlalchemy.py` | RF15, RNF11 |
| **`SimuladorTelemetria`** — *driving adapter* que chama a mesma porta que um GPS real; loop `asyncio` a 1 Hz (configurável), passeio aleatório dentro de `raio_metros`, frota espalhada em ~3 km em torno de Alegrete/RS, nunca derruba a API, `ligar()/desligar()/status()` | `adapters/inbound/simulador/simulador_telemetria.py` | RF16 aceite 2, RNF05 ("adapter GPS real futuro = outro adapter na mesma porta") |
| **`GerenciadorConexoes`** assinado no `PublicadorEventosEmMemoria` no *composition root*; fan-out JSON `{tipo, ocorrido_em, dados}`; descarta conexões mortas | `adapters/inbound/websocket/gerenciador_conexoes.py`, `infrastructure/di.py` | RF17, DEC-06 |
| `WS /v1/tempo-real?token=…` — token no *query string* (limitação do handshake em navegadores); inválido → `close(1008)` | `adapters/inbound/websocket/tempo_real_router.py` | RF17 aceite 3 |
| Rotas `GET/POST /v1/viaturas`, `PATCH /v1/viaturas/{id}/situacao`, `POST /v1/telemetria/posicoes`, `GET /v1/simulador`, `POST /v1/simulador/{ligar,desligar}` | `adapters/inbound/http/v1/viaturas_router.py` | RF15, RF16 |
| `montar_simulador(session_factory)` + singleton `simulador` desligado no *shutdown* do app | `infrastructure/di.py`, `main.py` | RF16 |
| Seed de 5 viaturas fictícias (`scripts/seed_viaturas.py`, chamado por `scripts/seed.py`) | `backend/scripts/` | RNF07 |
| 10 chaves i18n (`viatura.*`, `telemetria.*`) | `infrastructure/i18n/` | RNF08 |

## 3. Decisões tomadas durante a implementação

- **Posições não geram auditoria** (1 Hz × N viaturas inundaria `registros_auditoria`); mudanças de situação e despachos sim. Registrado como refinamento de RF20.
- **Telemetria HTTP exige papel `OPERADOR_CENTRAL`/`SUPERVISOR`** no MVP (não há "token de dispositivo"); o simulador em processo chama o caso de uso diretamente, sem HTTP — exatamente como um adapter de GPS real faria.
- **`EM_DESLOCAMENTO → OPERANDO`** existe no domínio (`chegar_ao_local`) mas não tem rota no MVP, conforme simplificação prevista na ETAPA-04 §2 (encerrar leva direto a `DISPONIVEL`).
- O canal WebSocket é **unidirecional** servidor → painel; mensagens do cliente servem apenas de *keep-alive*. Carga inicial continua sendo por REST (`GET /v1/viaturas`, `GET /v1/ocorrencias?status=VALIDADA`).
- A latência p95 < 1 s (RNF01\*) não foi **medida** nesta etapa (sem ambiente de rede); o teste ponta a ponta comprova a entrega sem *refresh*. A medição fica para a Etapa 8 / apresentação.

## 4. Testes

```
uv run pytest -q   →   156 passed
```

| Arquivo | Cobre |
| :--- | :--- |
| `tests/unit/domain/test_viatura_entity.py` (11) | normalização, obrigatórios, janela ±60 s (3 desvios) com posição anterior mantida, retroativa, sem fuso, `sinal`, ciclo despacho→operando→liberação, `INDISPONIVEL` manual e bloqueio de retirada de viatura despachada |
| `tests/unit/use_cases/test_viaturas.py` (7) | cadastro/listagem/auditoria, 409 prefixo e placa, RBAC, situação manual (inválida/transição/404), telemetria publica evento e mantém posição anterior, **simulador: `tick()` move só a frota ativa e dentro do raio (Haversine ≤ 100 m), liga/desliga com ≥ 2 ticks** |
| `tests/unit/adapters/test_eventos_e_websocket.py` (2) | fan-out com assinante quebrado isolado; gerenciador transmite, descarta conexão morta, serialização JSON |
| `tests/integration/test_viaturas_http.py` (4) | 409, listagem por qualquer papel, 403 para agente, situação manual, telemetria dentro/fora da janela, **simulador via API** (ligar → ticks → desligar → todas as viaturas com `sinal=OK`) |
| `tests/integration/test_tempo_real_ws.py` (2) | **token inválido/ausente → 1008**; painel conectado recebe `OcorrenciaValidada` (com coordenada) e `PosicaoAtualizada` disparados por chamadas HTTP, sem *refresh* |

## 5. Fora desta etapa

- Sugestão de viaturas próximas, ordem de despacho e encerramento → **Etapa 6**.
- Mapa Leaflet e cliente WS com reconexão exponencial → **Etapa 7**.
- Medição de latência e carga (≥ 10 viaturas, ≥ 5 painéis) → Etapa 8 / apresentação.

## 6. Rastreabilidade

RF-P08 ✅ (parcial: 3 de 5 capacidades) · RF-P12 ✅ (1 Hz configurável) · RNF-P02 ✅ (fila em memória atrás de porta) · RNF-P13 ✅ (parcial) · RNF-P15 ✅ · DEC-06 ✅ · RF15 ✅ · RF16 ✅ · RF17 ✅ (servidor; cliente na Etapa 7) · RNF04\* ✅ (backend) · HEX-10 ✅
