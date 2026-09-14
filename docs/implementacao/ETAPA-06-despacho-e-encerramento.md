# ETAPA 06 — Despacho tático atômico e encerramento (RF18, RF19, RNF11)

**Data:** 13/09/2026 · **Prioridade:** 🔴 (Must Have — Verificação 3: MVP ponta a ponta)

**Origem:** `ETAPA-04` §4 (RF18, RF19), §5 (RNF11), DEC-05; `ETAPA-05` NEXT-14; RF-P09, RF-P10, RF-P11, RNF-P13 (fallback tabular/manual).

## 1. Objetivo

Fechar as duas últimas capacidades do RF02: sugerir as viaturas mais próximas e emitir a ordem de despacho em uma única transação; e dar ao ciclo o estado final (`ENCERRADA`) que liberava as viaturas — inexistente na documentação original (RF-P10).

## 2. O que foi implementado

| Item | Arquivo | Requisito |
| :--- | :--- | :--- |
| Entidade `OrdemDeDespacho` (número `OD-AAAA-NNNNNN`, ocorrência, viatura, operador, data/hora, observações, `ativa`, `encerrada_em`) | `domain/despacho/entity.py` | RF18, critério 5 do MVP |
| **Serviço de domínio puro** `sugerir_viaturas_proximas(alvo, frota, agora, max_idade, qtd)` — filtra `DISPONIVEL` + posição válida (≤ 60 s), ordena por Haversine, desempata por prefixo | `domain/despacho/servico_proximidade.py` | RF18 aceite 1, DEC-05, RNF04\* |
| Evento `OrdemDeDespachoCriada` | `domain/despacho/eventos.py` | RF17 |
| Portas `RepositorioOrdemDespacho`, `GeradorNumeroOrdem`; portas de entrada `InterfaceSugerirViaturasProximas`, `InterfaceDespacharViatura`, `InterfaceEncerrarOcorrencia`, `InterfaceListarOrdensDespacho` | `application/ports/` | RF18, RF19 |
| `SugerirViaturasProximas` (exige ocorrência `VALIDADA`; devolve também `disponiveis_sem_posicao` para o **despacho manual** quando `sem_elegiveis`) | `application/use_cases/despacho/despachar_viatura.py` | RF18, RNF04\* |
| **`DespacharViatura`** — em uma única `UnidadeDeTrabalho`: ocorrência `VALIDADA → EM_ATENDIMENTO`, viatura `DISPONIVEL → EM_DESLOCAMENTO` (não-disponível → **409**), número sequencial, ordem, auditoria; commit; 3 eventos publicados depois do commit | idem | RF18 aceites 2–4, RNF11 |
| `ListarOrdensDespacho` | idem | RF18 |
| **`EncerrarOcorrencia`** — `EM_ATENDIMENTO → ENCERRADA` com desfecho; fecha ordens ativas e libera viaturas (→ `DISPONIVEL`); Operador ou Delegado | `application/use_cases/despacho/encerrar_ocorrencia.py` | RF19 |
| `OrdemDespachoModel`, `SequenciaOrdemDespachoModel`, migration `0003_ordens_despacho` (validada com `alembic check`) | `infrastructure/database/` | RF18 |
| `OrdemDespachoRepositorioSQLAlchemy`, `GeradorNumeroOrdemSQLAlchemy` (upsert atômico) | `adapters/outbound/persistence/ordem_despacho_repositorio_sqlalchemy.py` | RF18 |
| Rotas `GET /v1/ocorrencias/{id}/sugestoes-viaturas`, `POST /v1/despachos`, `GET /v1/despachos`, `POST /v1/ocorrencias/{id}/encerrar` | `adapters/inbound/http/v1/despacho_router.py` | RF18, RF19 |
| Correção transversal: `request_id` agora sobrevive até o handler de 500 (`request.state`) e vai no header `X-Request-ID` das respostas de erro | `adapters/inbound/http/{middleware,erros}.py` | RNF09 |

## 3. Decisões tomadas durante a implementação

- **Despacho de múltiplas viaturas (RF-P11) ficou fora do MVP**, como recomendado: uma ordem = uma viatura. O modelo (ordens N:1 ocorrência) já permite várias ordens ativas; `EncerrarOcorrencia` libera todas.
- **Viatura não-`DISPONIVEL` → 409** (`ConflitoError`), conforme critério de aceite; ocorrência não-`VALIDADA` → 422 (`TransicaoInvalidaError`), pois é erro de estado do agregado.
- **Despacho manual** de viatura sem posição válida é permitido (RNF04\*): o painel mostra `disponiveis_sem_posicao` quando não há elegíveis.
- Sequência de ordens em tabela própria (`sequencias_ordem_despacho`) em vez de generalizar `sequencias_protocolo` — evita alterar chave primária de tabela existente via migration.
- O teste de atomicidade injeta um gerador de número quebrado **no meio** da transação e verifica no banco que ocorrência, viatura e ordens ficaram intocadas (aceite 4 do RF18).

## 4. Testes

```
uv run pytest -q   →   176 passed
```

| Arquivo | Cobre |
| :--- | :--- |
| `tests/unit/domain/test_servico_proximidade.py` (4) | ordenação com distâncias conhecidas (0 km / ~0,8 km / ~2 km / ~13 km), limite 3, exclusão de sem posição / sem sinal (61 s) / despachada / indisponível, inclusão no limite (60 s), lista vazia, desempate |
| `tests/unit/use_cases/test_despacho.py` (12) | sugestões e `disponiveis_sem_posicao`, exige `VALIDADA` + Operador, sinal velho → `sem_elegiveis`, **despacho atômico** (ordem, dois agregados, auditoria, 3 eventos, listagem), manual sem GPS, 409 viatura ocupada, 422 não validada, RBAC, **rollback em falha no meio**, encerramento libera viatura/fecha ordem/audita/publica, exige `EM_ATENDIMENTO`, agente não encerra |
| `tests/integration/test_despacho_http.py` (4) | **fluxo MVP ponta a ponta via HTTP** (registrar → validar → sugestões → despacho → estados → ordem com os 4 campos do critério 5 → viatura some das sugestões → 409 → encerrar → viatura volta às sugestões), despacho manual sem elegíveis, **atomicidade verificada no banco após 500**, desfecho obrigatório e RBAC |

## 5. Fora desta etapa

- Painel tático (mapa, lista de validadas, botão de despacho) → **Etapa 7**.
- `EM_DESLOCAMENTO → OPERANDO` (chegada ao local) sem rota no MVP.

## 6. Rastreabilidade

RF-P08 ✅ (5/5 capacidades) · RF-P09 ✅ · RF-P10 ✅ · RF-P11 (decisão: fora do MVP) · RNF-P13 ✅ (fallback manual) · RF18 ✅ · RF19 ✅ · RNF11 ✅ · RF02 ✅ (guarda-chuva completo no backend)
