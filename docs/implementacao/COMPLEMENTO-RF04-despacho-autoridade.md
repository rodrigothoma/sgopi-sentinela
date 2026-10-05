# Complemento RF04 — Despacho da Autoridade na Validação

## Objetivo

Fechar a lacuna entre o passo 6 do UC04 e a implementação executável. O despacho opcional digitado pelo Delegado passa a ser enviado, normalizado, persistido, auditado e apresentado posteriormente no detalhe da ocorrência.

## Gap anterior

A interface já apresentava um campo de texto durante a revisão, porém a ação positiva de validação não enviava seu conteúdo. O endpoint não recebia corpo, o caso de uso descartava o texto e o domínio zerava `justificativa_revisao`; consequentemente, o despacho não aparecia no agregado, no histórico, na auditoria nem na consulta posterior.

## Regras preservadas

- Somente o papel `DELEGADO` pode validar.
- O despacho da autoridade é opcional.
- Espaços externos são removidos; texto vazio ou composto apenas por espaços é tratado como ausente.
- Devolução e rejeição continuam utilizando justificativa obrigatória.
- A transição permanece `AGUARDANDO_REVISAO` → `VALIDADA`.
- A composição do `hash_narrativa` não foi alterada.

## Arquitetura Hexagonal

| Camada | Implementação |
| :--- | :--- |
| Domínio | `Ocorrencia.validar(..., despacho)` normaliza o texto, aplica a transição e registra a decisão. |
| Porta inbound | `ValidarOcorrenciaInput` transporta o despacho opcional sem confundi-lo com a justificativa de devolução/rejeição. |
| Caso de uso | `ValidarOcorrencia` orquestra RBAC, domínio, persistência, auditoria, transação e publicação do evento. |
| Adapter HTTP | `POST /v1/ocorrencias/{id}/validar` aceita o corpo opcional `{ "despacho": string | null }`. |
| Porta e adapter outbound | `RepositorioOcorrencia` e seu adapter SQLAlchemy persistem o agregado e acrescentam a nova entrada histórica. |
| Frontend | A fila do Delegado envia o texto e o detalhe o identifica como **Despacho da autoridade** quando a transição tem destino `VALIDADA`. |
| Auditoria | A operação `ocorrencia.validar` registra `dados_depois.despacho`. |

## Persistência e ausência de migration

A implementação reutilizou integralmente o schema físico existente. Não foram criadas tabelas, colunas ou migrations.

- `ocorrencias.justificativa_revisao`: espelha o despacho da validação no agregado para consulta do detalhe;
- `historico_status_ocorrencia.justificativa`: preserva o despacho associado à transição para `VALIDADA`, com ator e data/hora, em tabela *append-only*;
- `registros_auditoria.dados_depois`: registra o despacho da operação sensível `ocorrencia.validar`.

O histórico é o registro temporal autoritativo da decisão; a auditoria é a trilha de conformidade. O campo do agregado oferece a projeção atual usada pelo detalhe da ocorrência.

## Consulta posterior

O detalhe devolve `justificativa_revisao` e `historico_status[].justificativa`. O frontend apresenta o texto como **Despacho da autoridade** quando a entrada histórica tem destino `VALIDADA`. Após a transação e um novo carregamento, o Delegado e o Agente autor conseguem consultar o despacho preservado.

## Testes e evidências

- `backend/tests/unit/domain/test_ocorrencia_entity.py`: despacho, normalização, ausência opcional e preservação do hash;
- `backend/tests/unit/use_cases/test_revisar_e_corrigir_ocorrencia.py`: persistência pelo caso de uso, auditoria, evento e RBAC;
- `backend/tests/integration/test_revisao_http.py`: contrato HTTP, consulta posterior, histórico, auditoria, limite e despacho vazio;
- `backend/tests/integration/test_persistencia_ocorrencia.py`: round-trip pelo repositório SQLAlchemy;
- `frontend/cypress/e2e/validacao-despacho.cy.ts`: validação pela interface, histórico, recarga e consulta pelo Agente autor.

O fluxo também foi verificado manualmente: o Delegado informou o despacho, validou a ocorrência, recarregou o detalhe e o Agente autor consultou o texto posteriormente.

## Rastreabilidade

`RF04` → `UC04` passo 6 → `ValidarOcorrenciaInput` → `ValidarOcorrencia` → `Ocorrencia.validar` → `RepositorioOcorrencia` → `ocorrencias.justificativa_revisao` / `historico_status_ocorrencia` / `registros_auditoria` → detalhe da ocorrência → testes automatizados e verificação manual.

## Commits da implementação

- `7f2c59c` — backend, domínio, porta inbound, caso de uso, HTTP e auditoria;
- `81e71a8` — frontend, envio e apresentação posterior;
- `d864d92` — testes de domínio, aplicação, persistência, HTTP e E2E.
