# ETAPA 04 — Consulta, revisão pelo Delegado e correção pelo Agente (RF13, RF04\*, RF14, RF20)

**Data:** 13/09/2026 · **Branch:** `matheus-Fastapi` · **Prioridade:** 🔴 (Must Have — Verificação 2: "registrar + validar ao vivo")
**Origem:** `ETAPA-04` §3 (RF04\*), §4 (RF13, RF14, RF20); `ETAPA-05` NEXT-08, NEXT-09; HEX-01; DIV-13; RF-P07, RF-P15, RF-P17, RF-P18, RF-P20; RNF10 (parcial).

## 1. Objetivo

Fechar o ciclo Agente ⇄ Delegado por completo: fila de triagem, detalhe com histórico, as três decisões com justificativa, e o caminho de volta (correção e reenvio) que a documentação original nunca fechava (RF-P07).

## 2. O que foi implementado

| Item | Arquivo | Requisito |
| :--- | :--- | :--- |
| Portas de entrada `InterfaceListarOcorrencias`, `InterfaceObterDetalheOcorrencia` + DTOs (`PaginaOcorrenciasOutput`, `OcorrenciaDetalheOutput` com `historico_status`, `narrativa_integra`) | `application/ports/inbound/interface_consultar_ocorrencias.py` | RF13 |
| Portas `InterfaceValidarOcorrencia`, `InterfaceDevolverParaCorrecao`, `InterfaceRejeitarOcorrencia`, `InterfaceCorrigirOcorrencia`, `InterfaceReenviarOcorrencia` | `application/ports/inbound/interface_revisar_ocorrencia.py` | RF04\*, RF14 |
| `ListarOcorrencias` (filtro multi-status, ordem `criada_em` asc, paginação com teto 200, **Agente só vê as próprias**), `ObterDetalheOcorrencia` (404; Agente não-autor → 403) — corrige o `GET` que chamava o repositório direto do adapter (HEX-01) | `application/use_cases/ocorrencia/consultar_ocorrencias.py` | RF13, HEX-01 |
| Mapeador entidade → DTO com **máscara de CPF** para papéis ≠ Delegado/Agente autor | `application/use_cases/ocorrencia/_mapeadores.py` | RNF10 |
| `ValidarOcorrencia`, `DevolverParaCorrecao`, `RejeitarOcorrencia` (base comum: papel → transação → transição → `salvar` → auditoria com `dados_antes/depois` → commit → evento) | `application/use_cases/ocorrencia/revisar_ocorrencia.py` | RF04\*, RF20, RNF11 |
| `CorrigirOcorrencia` (edição parcial; coordenada mesclada com a existente), `ReenviarOcorrencia` | `application/use_cases/ocorrencia/corrigir_ocorrencia.py` | RF14 |
| `ConsultarAuditoria` + `GET /v1/auditoria` (Delegado/Supervisor) | `application/use_cases/auditoria/`, `adapters/inbound/http/v1/auditoria_router.py` | RF20 aceite 1 |
| Rotas `GET /v1/ocorrencias`, `GET /{id}`, `POST /{id}/validar`, `POST /{id}/devolver`, `POST /{id}/rejeitar`, `PUT /{id}`, `POST /{id}/reenviar` | `adapters/inbound/http/v1/ocorrencias_router.py` | RF13, RF04\*, RF14 |
| Wiring dos 8 casos de uso novos | `infrastructure/di.py` | HEX-02 |

## 3. Decisões tomadas durante a implementação

- **Ordenação por "gravidade" (UC04 passo 2) foi removida** conforme DIV-13/RF-P17 — não há atributo de gravidade no modelo; a fila é apenas por antiguidade.
- **Agente não vê ocorrências de outros agentes** (lista e detalhe). Delegado, Operador e Supervisor veem todas. Regra aplicada no caso de uso, não no router.
- Eventos de domínio são publicados **após** o commit (nunca antes), para que o painel em tempo real não receba estado não confirmado.
- `narrativa_integra` é calculado na leitura comparando o hash gravado na validação — qualquer adulteração direta no banco ficaria visível (base para RF08).
- **RNF10 antecipado**: como o mapeador de saída já concentrava os campos, a máscara de CPF por papel entrou aqui em vez da Etapa 8.

## 4. Testes

```
uv run pytest -q   →   129 passed
```

| Arquivo | Cobre |
| :--- | :--- |
| `tests/unit/use_cases/test_consultar_ocorrencias.py` (6) | ordem da fila, visibilidade por papel, paginação/teto, status inválido, máscara de CPF por papel, 404/403 |
| `tests/unit/use_cases/test_revisar_e_corrigir_ocorrencia.py` (9) | validar (delegado, hash, auditoria antes/depois, evento, commit), só delegado decide, 404, decisão dupla → 422 + rollback sem 2º evento, justificativa mínima, rejeição terminal, **ciclo completo devolver→corrigir→reenviar→validar** (versão 5, histórico com 4 entradas), edição fora de `EM_CORRECAO`, correção sem envolvidos |
| `tests/integration/test_revisao_http.py` (9) | fila filtrada/ordenada e multi-status, agente2 não vê/403, operador vê CPF mascarado, 404, **Operador validando → 403 auditado**, validar 2× → 422 com `status_atual`, fluxo HTTP completo de correção (justificativa visível ao autor, 403 para outro agente, PUT parcial, reenvio, validação, histórico), edição fora de correção, rejeição terminal, `GET /v1/auditoria` por entidade (Delegado) e 403 para Agente |

## 5. Fora desta etapa

- Notificação in-app ao Agente (RF21, *Should*) — o evento `OcorrenciaDevolvida` já carrega `agente_policial_id` para um adapter futuro.
- Evidências digitais (RF22, *Should*).
- Telas de fila e decisão → **Etapa 7**.

## 6. Rastreabilidade

RF-P07 ✅ · RF-P15 ✅ · RF-P17 ✅ · RF-P18 ✅ · RF-P19 (evento publicado; notificação persistida é RF21) · RF-P20 ✅ · DIV-13 ✅ · HEX-01 ✅ · RF04\* ✅ · RF13 ✅ · RF14 ✅ · RF20 ✅ · RNF10 ✅ (respostas; logs na Etapa 8)
