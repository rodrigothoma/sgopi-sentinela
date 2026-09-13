# ETAPA 05 — Consolidação: o que foi encontrado, o que ficou fora do escopo e próximas implementações

**Objetivo da etapa:** fechar a análise com três listas explícitas — (1) achados, (2) itens deliberadamente deixados de lado por fugirem ao escopo do prompt, (3) sugestões de implementação em ordem recomendada, alinhadas ao calendário do `PLANEJAMENTO_DESENVOLVIMENTO.md`.

---

## 1. O que foi encontrado (síntese)

### 1.1 Números

| Categoria | Quantidade | Onde |
| :--- | :---: | :--- |
| Divergências doc × doc / doc × código | 31 (`DIV-01`…`DIV-31`) | Etapa 1 |
| Problemas em requisitos funcionais | 31 (`RF-P01`…`RF-P31`) | Etapa 2 |
| Capacidades sem requisito | 14 (A1–A14) | Etapa 2 §2 |
| Problemas em requisitos não funcionais | 18 (`RNF-P01`…`RNF-P18`) | Etapa 3 |
| RNFs ausentes | 9 (B1–B9) | Etapa 3 §2 |
| Decisões de base propostas | 9 (`DEC-01`…`DEC-09`) | Etapa 4 §1 |
| Requisitos funcionais novos | 12 (`RF11`…`RF22`) + 3 reescritos | Etapa 4 §3–4 |
| Requisitos não funcionais novos | 7 (`RNF06`…`RNF12`) + 5 reescritos | Etapa 4 §5 |
| Lacunas hexagonais no código | 14 (`HEX-01`…`HEX-14`) | Etapa 4 §6 |

### 1.2 Os cinco achados que mais importam

1. **Não existe uma máquina de estados única da ocorrência** (DIV-03). Há quatro versões (§3.2, enum do diagrama, UC02/UC04, código). É o achado com maior risco de "erro de lógica" nas Sprints 3 e 4, porque três fatias diferentes (S4, D6 e o encerramento) dependem dela. Proposta unificada na Etapa 4 §2.
2. **A ocorrência do código não tem coordenada geográfica** (DIV-16). Sem `latitude/longitude`, nada da Sprint 4 (mapa, proximidade, despacho) é possível. O diagrama de classes já previa os atributos; a fatia vertical foi escrita sem eles.
3. **RF02 é um requisito-iceberg** (RF-P08). Ele esconde cinco capacidades (frota, telemetria, tempo real, proximidade, ordem) que o Planejamento conhece (D1–D6), mas que não têm requisito, critério de aceite nem rastreabilidade.
4. **Autenticação/RBAC (RNF02) não tem RF e não tem código** (RNF-P04, DIV-20). O critério de aceite 2 do MVP ("somente Delegado valida") é inatingível até a Sprint 3 entregar S1/S2 — e o `agente_policial_id` vindo do body é uma falha de segurança que precisa sair antes da demo.
5. **A documentação carrega resquícios da concepção Java/Spring e um parágrafo de Firestore** (DIV-01, DIV-02). Não bloqueia código, mas contradiz o README, o mapeamento relacional e o `pyproject.toml`, e será cobrado na apresentação final (F5: "documento sem divergências com o que roda").

### 1.3 O que está **bom** e deve ser preservado

- A fatia vertical do UC01 está corretamente separada em domínio → porta → caso de uso → adapter, com testes unitários usando *fake* de repositório (15 testes, todos passando). É o molde certo para as demais fatias.
- A "regra de ouro" (domínio sem libs) está sendo respeitada no que existe.
- O i18n pt/en (backend e frontend) já está pronto — só falta o requisito que o ampare (RNF08).
- O diagrama de pacotes hexagonal é um bom mapa de portas: todas as portas propostas na Etapa 4 (`PortaAuditoria`, `InterfaceSinalGPS`, `InterfaceNotificacao`…) já estão nele com outro nome.
- O Planejamento por fatias verticais com "prova na segunda" é aderente ao MVP; a Etapa 4 apenas dá a cada fatia o requisito que faltava.

---

## 2. O que foi deixado de lado (fora do escopo deste prompt)

Itens identificados durante a análise, mas **não tratados** porque o prompt pedia análise de requisitos e prontidão do MVP, não implementação nem revisão completa de todos os módulos. Registrados para que ninguém suponha que foram esquecidos.

| # | Item | Motivo de exclusão | Onde retomar |
| :--- | :--- | :--- | :--- |
| E1 | **Alterar o código** (aplicar HEX-01…HEX-14, DEC-02, DEC-03) | O prompt pede análise e documentação; alterações de código exigem decisão da equipe sobre as DEC-nn. | NEXT-01 em diante |
| E2 | **Editar `DOCUMENTACAO_DE_ENGENHARIA.md`, `PLANEJAMENTO_DESENVOLVIMENTO.md` ou o README** (além de um link para esta pasta) | Mesma razão: as reescritas são propostas; a Sprint 5 (F5) é o momento planejado para alinhar documentação e código. | NEXT-14 |
| E3 | **Redesenhar diagramas** (casos de uso com UC12, sequências hexagonais, classes com `Coordenada`, enum de status) | Artefatos gráficos (PNG) fora da capacidade de edição desta análise; requer a ferramenta original (Astah/Visual Paradigm). | NEXT-14 |
| E4 | **Análise detalhada de sq03, sq05–sq11** | Casos de uso Should/Could/Won't, fora do MVP. Só foram verificados quanto à existência e ao ator. | Ciclo pós-MVP |
| E5 | **Requisitos detalhados para RF03, RF05–RF10** (cadeia de custódia, KDE de manchas, emissão de PDF/QR, ICP-Brasil, inquéritos, medidas protetivas, interagências) | Fora do MVP. Apenas os problemas de qualidade do enunciado foram apontados (Etapa 2). | Ciclo pós-MVP |
| E6 | **RNFs de disponibilidade, backup, retenção e compatibilidade de navegador** (B8, B9) | Sem valor demonstrável num MVP acadêmico de 4 sprints. | Ciclo pós-MVP |
| E7 | **Modelo de pessoa reutilizável entre ocorrências** (N:N `EnvolvidoOcorrencia`, subtipos `Vitima/Suspeito/Testemunha` com atributos próprios) | DEC-04 mantém 1:N no MVP; a mudança de modelo é pré-requisito de RF05/RF06, não do MVP. | Antes de RF05 |
| E8 | **Revisão de segurança do frontend** (XSS, armazenamento do token, CSP) | Só existe uma página; a revisão faz sentido após S1/S2. | Sprint 5 |
| E9 | **Avaliação de desempenho real** (medir p95 do WebSocket, carga do simulador) | Não há código de tempo real para medir. | Após D3/D4 |
| E10 | **Testes de integração e E2E** (pasta `tests/integration/` está vazia; Selenium prometido em F1/F2) | Fora do prompt; anotado como lacuna em RNF06. | Sprint 5 |
| E11 | **Ajustes de CORS/credenciais** (DIV-25) e **seed que roda antes das tabelas** (DIV-23) | São bugs de infraestrutura, não de requisito; anotados para correção rápida. | NEXT-02 |
| E12 | **Conteúdo da Wiki do GitHub** | Não acessada (externa ao repositório). | — |

---

## 3. Sugestões de próximas implementações (ordem recomendada)

A ordem respeita o calendário: Verificação 2 (21/09) exige registrar + validar ao vivo; Verificação 3 (28/09) exige o MVP ponta a ponta com **escopo congelado**. Os itens marcados 🧱 são pré-requisitos estruturais que, se atrasarem, atrasam tudo o que vem depois.

### Bloco 0 — Decidir (antes de qualquer código da Sprint 3; ~1 reunião)

| ID | Ação | Resolve | Responsável sugerido |
| :--- | :--- | :--- | :--- |
| **NEXT-00** | Reunião de 1 h para **aprovar/ajustar DEC-01…DEC-09** e a máquina de estados da Etapa 4 §2. Registrar a ata em `docs/analise/DECISOES.md`. | Todas as divergências bloqueantes | Equipe inteira (Princípio 03: contratos antes do código) |

### Bloco 1 — Fundação estrutural (início da Sprint 3; 1–2 dias) 🧱

| ID | Ação | Requisito | Lacuna | Toca |
| :--- | :--- | :--- | :--- | :--- |
| **NEXT-01** | Refatorar `StatusOcorrencia` para os 6 estados + tabela de transições; métodos `validar`, `devolver_para_correcao(justificativa)`, `rejeitar(justificativa)`, `reenviar`, `despachar`, `encerrar`; estado inicial `AGUARDANDO_REVISAO`; `historico_status`. Atualizar testes. | RF04\*, RF14, RF19 | HEX-04 | `domínio` `testes` |
| **NEXT-02** | Adicionar `Coordenada` (VO com validação de faixa) + `data_hora_fato` à `Ocorrencia`, ao DTO, ao schema, ao model e ao formulário. Corrigir CORS (lista de origens) e mover o seed para script Python (`scripts/seed.py`). | RF01\*, DEC-03 | HEX-05, DIV-23, DIV-25 | `domínio` `adapters` `frontend` |
| **NEXT-03** | Configurar **Alembic** (env async), gerar migration inicial, remover `create_all` do `lifespan`. | RNF07 | HEX-11, DIV-21 | `infra` |
| **NEXT-04** | Introduzir portas `Relogio`, `GeradorProtocolo`, `UnidadeDeTrabalho`, `PortaAuditoria`, `PublicadorEventos` (ABCs + fakes). Mover *wiring* para `infrastructure/di.py`; routers dependem das portas. Handler global para `DomainError` → 422 i18n. | RNF05\*, RNF11, RF20 | HEX-02/03/07/08/09/10 | `aplicação` `infra` |
| **NEXT-05** | Invariante "≥ 1 envolvido" via *factory* `Ocorrencia.registrar(...)`; remover cascatas de exclusão do ORM; adicionar `versao`/`atualizada_em`. | RF01\*, RNF03\* | HEX-06, HEX-12 | `domínio` `banco` |

### Bloco 2 — Sprint 3: registro e validação (15–20/09)

| ID | Ação | Requisito | Planejamento |
| :--- | :--- | :--- | :--- |
| **NEXT-06** | Login/JWT: `Usuario`, `Papel`, `RepositorioUsuario`, `HasherSenha`, `ProvedorToken`, `POST /v1/auth/login`, `usuario_atual()`; remover `agente_policial_id` do body. Seed com 3 usuários. | RF11, RF12 | S1 |
| **NEXT-07** | `exigir_papel()` nas rotas + checagem no caso de uso + auditoria de negação; UI esconde ações por papel. | RF12, RNF02\*, RF20 | S2 |
| **NEXT-08** | `ListarOcorrencias` (filtro por status, ordenação, paginação) + `ObterDetalheOcorrencia`; tela de fila do Delegado. | RF13 | S3 |
| **NEXT-09** | `ValidarOcorrencia`, `DevolverParaCorrecao`, `RejeitarOcorrencia` (justificativa obrigatória) + endpoints + tela de decisão; `CorrigirOcorrencia`/`ReenviarOcorrencia` + tela do Agente. | RF04\*, RF14 | S4 |
| **NEXT-10** | Evidências (porta `ArmazenamentoArquivos`, adapter disco, validação de formato/tamanho, hash) — **Should**: entra se S1–S4 estiverem verdes até quinta. | RF22 | S6 |

### Bloco 3 — Sprint 4: despacho tático (22–27/09)

| ID | Ação | Requisito | Planejamento |
| :--- | :--- | :--- | :--- |
| **NEXT-11** | `Viatura` + `SituacaoViatura` + `RepositorioViatura` + CRUD mínimo + tela de frota. | RF15 | D1 |
| **NEXT-12** | `RegistrarPosicaoViatura` + `POST /v1/telemetria` + **simulador como adapter de entrada** com liga/desliga; `PublicadorEventosEmMemoria`. | RF16 | D2 |
| **NEXT-13** | `WS /v1/tempo-real` + `GerenciadorConexoes` + cliente com reconexão; mapa Leaflet com carga inicial REST + atualizações WS. | RF17, RNF01\*, RNF04\* | D3, D4 |
| **NEXT-14** | `calcular_distancia_km` (Haversine, teste com coordenadas conhecidas) + `SugerirViaturasProximas` (filtro 60 s) + `DespacharViatura` atômico via `UnidadeDeTrabalho` + `OrdemDeDespacho` + `EncerrarOcorrencia`. | RF18, RF19, RNF11 | D5, D6 |

### Bloco 4 — Sprint 5: qualidade e entrega (29/09–04/10)

| ID | Ação | Requisito | Planejamento |
| :--- | :--- | :--- | :--- |
| **NEXT-15** | `pytest-cov` com *threshold* 80 % em `domain`+`application`; `import-linter`; testes de integração com Postgres; E2E Selenium do UC01/UC04/UC02. | RNF05\*, RNF06 | F1, F2, F3 |
| **NEXT-16** | `/health` com verificação de banco; logs JSON com `request_id`; corpo de erro padronizado. | RNF09 | T1 (pendente) |
| **NEXT-17** | Máscara de CPF por papel e em logs; nota de base legal LGPD. | RNF10 | — |
| **NEXT-18** | **Alinhar a documentação** (F5): aplicar DEC-01/02 em §3.2, §4.2, §4.3; substituir a tabela de RFs/RNFs pelas versões reescritas + RF11–RF22 + RNF06–RNF12 (Etapa 4); regenerar o diagrama de classes (status, `Coordenada`, `Viatura`, `OrdemDeDespacho`, `Usuario/Papel`), o de casos de uso (UC12, ator de UC10) e as sequências sq01/sq02/sq04 mostrando porta → caso de uso → repositório; atualizar o "Estado atual do código" do Planejamento. | F5 | F5 |
| **NEXT-19** | Notificação in-app ao Agente — **Should**, só se houver folga. | RF21 | — |

### Pós-MVP (não planejar antes de 05/10)

- Modelo de pessoa reutilizável (E7) → pré-requisito de RF05/RF06.
- Emissão de documentos oficiais em PDF com chave/QR → pré-requisito de RF08.
- Abertura de inquérito → pré-requisito de RF06.
- Cadeia de custódia como eventos append-only → RF03.
- Porta `AssinaturaDigital` com adapter fake → RF07.
- Broker real (Redis/RabbitMQ) atrás de `PublicadorEventos` → RNF01 em produção.

---

## 4. Como usar esta pasta daqui em diante

- **Antes de cada sprint:** conferir se as decisões DEC-nn permanecem válidas; registrar mudanças em `DECISOES.md` (a ser criado em NEXT-00).
- **Em cada PR:** referenciar o ID do requisito (`RF13`, `RNF09`…) e, quando aplicável, a lacuna que fecha (`HEX-02`, `DIV-16`…). Isso dá a rastreabilidade RF → código que a Etapa 2 apontou como inexistente.
- **Na Sprint 5 (F5):** usar a Etapa 4 como *checklist* do que precisa migrar para `DOCUMENTACAO_DE_ENGENHARIA.md`; depois disso, esta pasta pode ser arquivada como histórico de decisão.

---

## O que foi feito nesta etapa

1. Consolidados os números e os cinco achados de maior impacto (§1).
2. Registrados **12 itens deliberadamente excluídos** do escopo (E1–E12), cada um com motivo e ponto de retomada (§2).
3. Propostas **20 ações** (`NEXT-00`…`NEXT-19`) em 5 blocos, mapeadas para os requisitos da Etapa 4, para as lacunas das Etapas 1–4 e para as tarefas do Planejamento (§3).
4. Definido o uso desta pasta como instrumento de rastreabilidade (§4).
5. Adicionada uma linha na tabela "Documentação Técnica" do `README.md` apontando para `docs/analise/00-INDICE-E-METODO.md` (única alteração fora desta pasta).
