# 🛠️ Rastreabilidade da Implementação do MVP — Índice

**Projeto:** SGOPI Sentinela · **Branch:** `matheus-Fastapi` · **Data:** 13/09/2026
**Origem:** as correções e requisitos apontados em [`docs/analise/`](../analise/00-INDICE-E-METODO.md) (Etapas 1–5) e no `README.md`.
**Método:** cada etapa implementa um bloco de requisitos por ordem de criticidade (bloqueantes primeiro), é testada, e gera um documento com *o que foi feito, decisões, testes e rastreabilidade* (IDs `DIV`, `RF-P`, `RNF-P`, `HEX`, `DEC`, `NEXT` da análise).

## Etapas

| # | Documento | Requisitos | Testes ao final |
| :---: | :--- | :--- | :---: |
| 1 | [Fundação do domínio](ETAPA-01-fundacao-dominio.md) | DEC-02/03/04/05/09, RF01\*, HEX-03…08 | 61 |
| 2 | [Infraestrutura e aderência hexagonal](ETAPA-02-infraestrutura-e-aderencia-hexagonal.md) | RNF03\*, RNF05\*, RNF07, RNF09, RNF11, HEX-02/09/11/12, DIV-21…25 | 75 |
| 3 | [Autenticação, papéis e auditoria](ETAPA-03-autenticacao-papeis-auditoria.md) | RF11, RF12, RF20, RNF02\* | 105 |
| 4 | [Consulta, revisão e correção](ETAPA-04-consulta-revisao-correcao.md) | RF13, RF04\*, RF14, RF20, RNF10 | 129 |
| 5 | [Frota, telemetria e tempo real](ETAPA-05-frota-telemetria-tempo-real.md) | RF15, RF16, RF17, RNF01\*, RNF04\*, DEC-06 | 156 |
| 6 | [Despacho e encerramento](ETAPA-06-despacho-e-encerramento.md) | RF18, RF19, RNF11 | 176 |
| 7 | [Frontend do MVP](ETAPA-07-frontend-mvp.md) | UI de RF01\*/04\*/11/13/14/15/16/17/18/19, RNF04\*, RNF08 | 176 (+ tsc/build + smoke ao vivo) |
| 8 | [Qualidade, observabilidade e documentação](ETAPA-08-qualidade-e-documentacao.md) | RNF05\*, RNF06, RNF09, RNF10, RNF12 | **240** · cobertura 98 % |

Complemento: [Nota LGPD / base legal](NOTA-LGPD-BASE-LEGAL.md).

## Status por requisito (visão consolidada)

| Requisito | Status | Onde |
| :--- | :---: | :--- |
| RF01\* Registro de ocorrência (coordenada, data do fato, ≥ 1 envolvido, protocolo sequencial, ator do token) | ✅ | Etapas 1, 3, 7 |
| RF02 Despacho tático (guarda-chuva de RF15–RF18) | ✅ | Etapas 5, 6, 7 |
| RF04\* Revisão pelo Delegado (validar / devolver / rejeitar com justificativa) | ✅ | Etapas 1, 4, 7 |
| RF11 Autenticação JWT 8 h | ✅ | Etapa 3 |
| RF12 Usuários e papéis (seed; RBAC auditado) | ✅ | Etapa 3 |
| RF13 Consulta paginada + detalhe com histórico | ✅ | Etapa 4 |
| RF14 Correção e reenvio pelo Agente autor | ✅ | Etapas 1, 4, 7 |
| RF15 Cadastro de viaturas | ✅ | Etapas 5, 7 |
| RF16 Telemetria + simulador (driving adapter) | ✅ | Etapas 5, 7 |
| RF17 Canal de tempo real (WS + cliente com *backoff*) | ✅ | Etapas 5, 7 |
| RF18 Sugestão Haversine + ordem de despacho atômica | ✅ | Etapas 6, 7 |
| RF19 Encerramento e liberação de viaturas | ✅ | Etapas 6, 7 |
| RF20 Auditoria append-only + consulta | ✅ | Etapas 2, 3, 4 |
| RF21 Notificação in-app (*Should*) | ⏳ | eventos já publicados; adapter pendente |
| RF22 Evidências digitais (*Should*) | ⏳ | não iniciado |
| RNF01\* Tempo real p95 < 1 s | ◐ | entrega sem *refresh* comprovada; **latência não medida** |
| RNF02\* Controle de acesso (argon2, JWT, CORS por lista) | ✅ | Etapas 2, 3 (HTTPS = deploy) |
| RNF03\* Imutabilidade (sem cascata, soft delete, trigger append-only, versão) | ✅ | Etapa 2 |
| RNF04\* Resiliência (janela 60 s, fallback tabular, reconexão, `/health` com DB) | ✅ | Etapas 2, 5, 7 |
| RNF05\* Desacoplamento verificado (`import-linter` + teste) | ✅ | Etapa 8 |
| RNF06 Testabilidade (fakes, cobertura ≥ 80 %) | ✅ | Etapas 1–8 |
| RNF07 Portabilidade (Alembic, seed por script, tudo via `.env`) | ✅ | Etapas 2, 3 |
| RNF08 i18n pt/en | ✅ | Etapas 2, 7 |
| RNF09 Observabilidade (`/health`, logs JSON, `request_id`, corpo de erro padrão) | ✅ | Etapas 2, 6, 8 |
| RNF10 LGPD (máscara de CPF por papel e em logs, seed fictício, nota de base legal) | ✅ | Etapas 4, 8 |
| RNF11 Integridade transacional (UoW, optimistic locking) | ✅ | Etapas 2, 6 |
| RNF12 Contrato de API (OpenAPI em `/docs`; tipos TS espelhados) | ✅ | Etapa 7 |

Legenda: ✅ implementado e testado · ◐ parcial · ⏳ pendente (fora do Must do MVP)

## O que ficou fora (e por quê)

| Item | Motivo | Retomar em |
| :--- | :--- | :--- |
| Execução contra **PostgreSQL real** | Docker inacessível neste ambiente; esquema validado por `alembic upgrade/check/downgrade` em SQLite e todos os tipos são portáveis | primeira execução com `docker compose up` |
| **Testes E2E em navegador** | sem navegador/Playwright disponível; frontend validado por `tsc`, `vite build` e smoke test do fluxo completo via proxy | Sprint 5 (F1/F2) |
| **Medição de latência p95** do WebSocket | precisa de rede e vários painéis | apresentação / Sprint 5 |
| RF21, RF22 (*Should*) | prioridade abaixo dos Must; portas e eventos já preparados | Sprint 3/5 se houver folga |
| Alinhar `DOCUMENTACAO_DE_ENGENHARIA.md` e diagramas (NEXT-18) | tarefa F5 da Sprint 5; as decisões e a máquina de estados estão registradas na Etapa 1 e na análise | Sprint 5 |
| Revogação de token antes da expiração | token stateless no MVP | pós-MVP |
