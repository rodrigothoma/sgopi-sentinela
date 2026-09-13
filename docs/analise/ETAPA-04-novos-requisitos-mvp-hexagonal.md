# ETAPA 04 — Requisitos novos/reescritos para o MVP e mapeamento na Arquitetura Hexagonal

**Objetivo da etapa:** responder à pergunta "o que precisa existir como requisito para que o MVP (§3 da Doc. de Engenharia) seja construível em Arquitetura Hexagonal?". Cada requisito proposto traz: justificativa rastreável (às Etapas 1–3), critérios de aceite verificáveis e o **mapeamento em portas, casos de uso e adaptadores**. Ao final, as lacunas de aderência hexagonal do código atual (HEX-nn).

> Os IDs continuam a numeração do documento original (RF11+, RNF06+) para não colidir. As reescritas de RF01/RF02/RF04 e RNF01–RNF05 são **propostas**; o documento original não foi alterado.

---

## 1. Decisões de base (pré-requisito para qualquer requisito abaixo)

Sem fechar estas decisões, os requisitos seguintes ficam ambíguos. Cada uma resolve uma divergência bloqueante da Etapa 1.

| ID | Decisão proposta | Resolve | Impacto no código |
| :--- | :--- | :--- | :--- |
| **DEC-01** | **Persistência = PostgreSQL 16 + SQLAlchemy 2 async + Alembic.** Remover Firestore/Firebase de §4.3 e JPA/Hibernate/STOMP/SockJS/`.jar`/`.xml` de §4.2 e do diagrama de implantação. | DIV-01, DIV-02 | Nenhum (código já está assim); configurar Alembic (DIV-21). |
| **DEC-02** | **Máquina de estados única da ocorrência** (ver §2 abaixo). | DIV-03, DIV-04, DIV-05, RF-P10, RF-P15 | Refatorar `StatusOcorrencia` e transições em `entity.py`. |
| **DEC-03** | **Ocorrência tem coordenada geográfica obrigatória** (`latitude`, `longitude` como *value object* `Coordenada`) e `data_hora_fato`. No MVP, a coordenada é digitada/clicada no mapa; geocodificação de endereço fica como porta futura. | DIV-16, RF-P02 | Novo VO + colunas + migration + campo no formulário. |
| **DEC-04** | **Envolvido permanece 1:N com a ocorrência no MVP** (não é pessoa reutilizável). Campos mínimos: `nome`, `tipo`, `documento` (CPF opcional, validado se presente). Modelo N:N e subtipos ricos ficam como dívida para RF05/RF06. | DIV-17, RF-P23 | Nenhum; registrar dívida. |
| **DEC-05** | **Distância = Haversine** sobre a última posição válida com idade ≤ 60 s (parametrizável). | DIV-07, RF-P09 | Serviço de domínio puro. |
| **DEC-06** | **Tempo real = WebSocket nativo do FastAPI**; eventos internos via porta `PublicadorEventos` com adapter em memória no MVP (broker é evolução). | RNF-P02 | Nova porta + adapter. |
| **DEC-07** | **Evidências no MVP: `pdf, jpg, jpeg, png`, ≤ 10 MB/arquivo, ≤ 10 arquivos/ocorrência**, armazenadas em disco local atrás da porta `ArmazenamentoArquivos`. | DIV-08, RF-P06 | Nova porta + adapter. |
| **DEC-08** | **Papéis do MVP: `AGENTE`, `DELEGADO`, `OPERADOR_CENTRAL`.** `SUPERVISOR`, `PERITO`, `ESCRIVAO` ficam no enum, sem UC no MVP. Acesso anônimo (Cidadão) não existe no MVP. | DIV-06, RNF-P05 | Enum `Papel` no domínio. |
| **DEC-09** | **Sem assinatura digital, PDF ou ICP-Brasil no MVP.** "Validação" = transição de estado + `validada_por_id` + registro de auditoria + hash SHA-256 da narrativa (opcional, barato). | RF-P18, RF-P20 | — |

---

## 2. Máquina de estados unificada da Ocorrência (proposta — DEC-02)

```
                 ┌──────────────────────────────────────────────┐
                 │                                              │ reenviar (Agente)
                 ▼                                              │
 [criar] ─► AGUARDANDO_REVISAO ──validar (Delegado)──► VALIDADA ──despachar (Operador)──► EM_ATENDIMENTO ──encerrar──► ENCERRADA
                 │                                                                                 (Operador/Delegado)
                 ├──devolver_para_correcao (Delegado, justificativa)──► EM_CORRECAO ──┘
                 │
                 └──rejeitar (Delegado, justificativa)──► REJEITADA  (terminal)
```

| Estado | Entra por | Sai por | Quem | Observação |
| :--- | :--- | :--- | :--- | :--- |
| `AGUARDANDO_REVISAO` | criação; reenvio após correção | validar / devolver / rejeitar | Agente cria; Delegado decide | Estado inicial **compulsório** (UC01 regra 3). Remove `REGISTRADA`/`EM_VALIDACAO` do código e `Rascunho` do §3.2. |
| `EM_CORRECAO` | devolver_para_correcao | reenviar | Agente edita | Justificativa obrigatória na devolução. Única janela em que a narrativa é editável. |
| `REJEITADA` | rejeitar | — | Delegado | Terminal. Justificativa obrigatória. Arquivada, nunca excluída. |
| `VALIDADA` | validar | despachar | Delegado → Operador | Narrativa congelada (hash). Aparece no painel tático. Corresponde a "Aguardando Atendimento" do diagrama de classes. |
| `EM_ATENDIMENTO` | despachar | encerrar | Operador | Existe ≥ 1 `OrdemDeDespacho` ativa. Substitui "Em Despacho" do §3.2. |
| `ENCERRADA` | encerrar | — | Operador/Delegado | Terminal. Libera viatura(s) para `DISPONIVEL`. Substitui "Concluída" do §3.2. |

**Máquina de estados da Viatura (nova):** `DISPONIVEL ⇄ EM_DESLOCAMENTO → OPERANDO → DISPONIVEL`; `INDISPONIVEL` entra/sai manualmente. Apenas `DISPONIVEL` pode ser despachada (UC02 regra 1). No MVP, `EM_DESLOCAMENTO → OPERANDO` pode ser simplificada (encerrar leva direto a `DISPONIVEL`).

---

## 3. Requisitos funcionais **reescritos** (Must Have)

### RF01 (reescrito) — Registro de Ocorrência Policial
O sistema deve permitir que um usuário autenticado com papel `AGENTE` registre uma ocorrência contendo: natureza, descrição do fato (obrigatória, ≥ 20 caracteres), data/hora do fato (não futura), endereço textual, **coordenada geográfica** (latitude ∈ [-90, 90], longitude ∈ [-180, 180]), **ao menos um envolvido** (nome + tipo ∈ {VÍTIMA, TESTEMUNHA, SUSPEITO}; CPF opcional e validado), zero ou mais tipificações penais. Ao registrar, o sistema gera protocolo único no formato `SGOPI-AAAA-NNNNNN`, grava o agente autor e a data/hora de registro e coloca a ocorrência em `AGUARDANDO_REVISAO`.

**Critérios de aceite:** (1) POST sem envolvido → 422 com mensagem i18n; (2) coordenada fora da faixa → 422; (3) protocolo único sob 1.000 inserções concorrentes; (4) estado inicial sempre `AGUARDANDO_REVISAO`; (5) `agente_policial_id` vem do token, nunca do body.

### RF02 (reescrito) — Despacho Tático
Desmembrado em RF15 (frota), RF16 (telemetria), RF17 (tempo real) e RF18 (sugestão + ordem de despacho). O RF02 passa a ser um requisito-guarda-chuva que referencia os quatro.

### RF04 (reescrito) — Revisão pelo Delegado
O sistema deve permitir que um usuário com papel `DELEGADO` consulte a fila de ocorrências em `AGUARDANDO_REVISAO` (ordenada da mais antiga para a mais nova), inspecione o detalhe e execute **uma** das três decisões: `validar`, `devolver_para_correcao` (justificativa obrigatória, ≥ 10 caracteres) ou `rejeitar` (justificativa obrigatória). Cada decisão registra o delegado, a data/hora e gera um registro de auditoria. Tentativa de decisão por outro papel devolve 403 e é auditada.

---

## 4. Requisitos funcionais **novos** para o MVP

Formato: **Descrição** · **Rastreabilidade** · **Critérios de aceite** · **Mapeamento hexagonal** (porta de entrada → caso de uso → portas de saída → adapters) · **MoSCoW no MVP**.

### RF11 — Autenticação e sessão (Must)
- **Descrição:** o sistema deve autenticar usuários por login e senha e emitir token JWT (validade 8 h) contendo `sub`, `papel` e `exp`; toda rota, exceto `/health` e `/auth/login`, exige token válido.
- **Rastreabilidade:** A1; pré-condição de UC01/02/04; §3.4 critério 2; Planejamento S1; DIV-20.
- **Aceite:** login inválido → 401; token expirado → 401; senha nunca em texto puro no banco (argon2/bcrypt).
- **Hexagonal:** `InterfaceAutenticarUsuario` → `AutenticarUsuario` → `RepositorioUsuario`, `HasherSenha`, `ProvedorToken` → adapters `UsuarioRepositorioSQLAlchemy`, `HasherArgon2`, `ProvedorTokenJose`. Adapter de entrada: `POST /v1/auth/login`; dependência FastAPI `usuario_atual()` que decodifica o token e devolve um DTO `UsuarioAutenticado(id, papel)` para os demais routers.

### RF12 — Usuários e papéis (Must, mínimo)
- **Descrição:** o sistema deve manter usuários com `nome`, `login` único, `senha_hash`, `papel` (enum DEC-08) e `ativo`. No MVP não há tela de cadastro: usuários são criados por **seed** (um por papel).
- **Rastreabilidade:** A2; RNF02; Planejamento S2, F4.
- **Aceite:** seed cria `agente`, `delegado`, `operador`; usuário inativo não autentica; rota de Delegado com token de Agente → 403 auditado.
- **Hexagonal:** entidade `Usuario` + enum `Papel` em `domain/usuario/`; `RepositorioUsuario`; autorização como dependência do adapter de entrada (`exigir_papel(Papel.DELEGADO)`), que apenas repassa `UsuarioAutenticado` ao caso de uso — a **regra** "só Delegado valida" também é verificada no caso de uso (defesa em profundidade).

### RF13 — Consulta de ocorrências (Must)
- **Descrição:** o sistema deve listar ocorrências filtradas por status (um ou vários), ordenadas por `data_hora_registro` ascendente, com paginação (`limit`/`offset`), e devolver o detalhe completo por ID (envolvidos, tipificações, evidências, histórico de status).
- **Rastreabilidade:** A3; UC04 passos 1–4; UC02 passo 2; Planejamento S3; DIV-13 (gravidade removida do MVP).
- **Aceite:** `GET /v1/ocorrencias?status=AGUARDANDO_REVISAO` devolve só esse status, mais antiga primeiro; detalhe inclui `historico_status[]`.
- **Hexagonal:** `InterfaceConsultarOcorrencias` → `ListarOcorrencias`, `ObterDetalheOcorrencia` → `RepositorioOcorrencia.listar(filtro, ordenacao, paginacao)`, `buscar_por_id`. Corrige DIV-29 (o `GET` atual pula o caso de uso).

### RF14 — Correção e reenvio pelo Agente (Must)
- **Descrição:** o Agente autor pode editar uma ocorrência em `EM_CORRECAO` (narrativa, envolvidos, tipificações, coordenada) e reenviá-la, voltando a `AGUARDANDO_REVISAO`. A justificativa do Delegado fica visível ao Agente.
- **Rastreabilidade:** A4; UC04 alt. I; RF-P07.
- **Aceite:** edição em qualquer outro estado → 422 `invalid_transition`; agente que não é o autor → 403; cada reenvio incrementa `versao` e grava histórico.
- **Hexagonal:** `InterfaceCorrigirOcorrencia` → `CorrigirOcorrencia`, `ReenviarOcorrencia` → `RepositorioOcorrencia`, `PortaAuditoria`.

### RF15 — Cadastro de viaturas (Must)
- **Descrição:** o sistema deve manter viaturas com `prefixo` único, `placa` única, `situacao` (enum §2) e `ultima_posicao` (coordenada + timestamp, opcional). Operador da Central lista e altera a situação manual (`DISPONIVEL ⇄ INDISPONIVEL`).
- **Rastreabilidade:** A5; UC02; Planejamento D1; diagrama de classes `Viatura`/`Situacao`.
- **Aceite:** prefixo duplicado → 409; viatura `EM_DESLOCAMENTO` não pode ser marcada `INDISPONIVEL` manualmente.
- **Hexagonal:** `domain/viatura/entity.py` (`Viatura`, `SituacaoViatura`); `InterfaceGerirViaturas` → `CadastrarViatura`, `AlterarSituacaoViatura`, `ListarViaturas` → `RepositorioViatura`.

### RF16 — Ingestão de telemetria GPS e simulador (Must)
- **Descrição:** o sistema deve receber posições (`viatura_id`, `lat`, `lon`, `timestamp`) por endpoint HTTP e/ou WebSocket, atualizar `ultima_posicao` da viatura e publicar evento `PosicaoAtualizada`. Um **simulador** (processo/adaptador separado, ligável pelo painel) emite posições a 1 Hz para todas as viaturas não-`INDISPONIVEL`, movendo-as aleatoriamente dentro de um raio configurável.
- **Rastreabilidade:** A6; §3.2 "serviço de simulação"; UC02 pré-cond. 2; Planejamento D2; RNF01.
- **Aceite:** posição com timestamp > 60 s no futuro/passado → rejeitada; painel liga/desliga simulador; posição anterior é mantida se a nova for inválida (RNF04).
- **Hexagonal:** `InterfaceReceberTelemetria` → `RegistrarPosicaoViatura` → `RepositorioViatura`, `PublicadorEventos`, `Relogio`. O **simulador é um adapter de entrada** (*driving adapter*) que chama a mesma porta — o domínio não sabe se a posição é real ou simulada. Adapter GPS real futuro = outro adapter na mesma porta (RNF05 atendido de fato).

### RF17 — Canal de tempo real (Must)
- **Descrição:** o sistema deve expor `WS /v1/tempo-real` que envia ao painel os eventos `PosicaoAtualizada`, `OcorrenciaValidada`, `OcorrenciaDespachada`, `ViaturaSituacaoAlterada`; o cliente reconecta automaticamente com *backoff* e, ao (re)conectar, obtém a carga inicial por REST.
- **Rastreabilidade:** A7; §3.3 passo 3; §3.4 critério 3; Planejamento D3/D4; RNF01/RNF04.
- **Aceite:** posição chega ao navegador em < 1 s (p95, rede local) sem *refresh*; derrubar o servidor e subir → cliente reconecta sozinho; token inválido no *handshake* → conexão recusada.
- **Hexagonal:** porta de saída `PublicadorEventos.publicar(evento)`; adapter `PublicadorEventosEmMemoria` que faz *fan-out* para o `GerenciadorConexoesWebSocket` (adapter de entrada/saída em `adapters/inbound/websocket/`). Casos de uso só chamam a porta.

### RF18 — Sugestão de viaturas próximas e ordem de despacho (Must)
- **Descrição:** para uma ocorrência `VALIDADA`, o sistema deve calcular (Haversine) a distância de todas as viaturas `DISPONIVEL` com posição válida (≤ 60 s) e devolver as 3 mais próximas; o Operador confirma uma viatura e o sistema, **atomicamente**, cria `OrdemDeDespacho` (número único, data/hora, operador, viatura, ocorrência, observações), muda viatura → `EM_DESLOCAMENTO`, ocorrência → `EM_ATENDIMENTO`, audita e publica evento. Se não houver viatura elegível, informa e permite despacho manual por viatura escolhida (RNF04).
- **Rastreabilidade:** A8; UC02 passos 4–9; §3.4 critérios 3/5; Planejamento D5/D6; DEC-05.
- **Aceite:** ordem das sugestões correta em teste unitário com coordenadas conhecidas; despacho de viatura não-`DISPONIVEL` → 409; falha no meio da transação não deixa ocorrência `EM_ATENDIMENTO` sem ordem; ordem contém os 4 campos do critério 5.
- **Hexagonal:** serviço de domínio puro `calcular_distancia_km(a: Coordenada, b: Coordenada)` em `domain/shared/geo.py`; `InterfaceDespacharViatura` → `SugerirViaturasProximas`, `DespacharViatura` → `RepositorioOcorrencia`, `RepositorioViatura`, `RepositorioOrdemDespacho`, `UnidadeDeTrabalho`, `PortaAuditoria`, `PublicadorEventos`, `Relogio`.

### RF19 — Encerramento do atendimento (Must, simplificado)
- **Descrição:** Operador ou Delegado encerra uma ocorrência `EM_ATENDIMENTO` informando um desfecho textual; a ocorrência vai para `ENCERRADA` e as viaturas da(s) ordem(ns) ativa(s) voltam para `DISPONIVEL`.
- **Rastreabilidade:** A9; RF-P10; §3.2 (estado final).
- **Aceite:** encerrar sem desfecho → 422; viatura volta a aparecer nas sugestões de outro despacho.
- **Hexagonal:** `InterfaceEncerrarOcorrencia` → `EncerrarOcorrencia` → mesmas portas de RF18.

### RF20 — Auditoria de operações sensíveis (Must, mínimo)
- **Descrição:** toda transição de estado de ocorrência e viatura, toda ordem de despacho e toda tentativa negada de autorização geram um `RegistroAuditoria` (`quem`, `quando`, `operacao`, `entidade`, `entidade_id`, `dados_antes`, `dados_depois`, `ip`), em tabela sem UPDATE/DELETE.
- **Rastreabilidade:** A10; RNF03; UC02 passo 9; UC04 passos 8 e exc. I; DIV-24.
- **Aceite:** `GET /v1/auditoria?entidade_id=…` (Delegado) lista os eventos; tentativa de `DELETE` na tabela pelo *role* da aplicação falha.
- **Hexagonal:** porta `PortaAuditoria.registrar(evento)`; adapter `AuditoriaSQLAlchemy` (append-only). Casos de uso chamam a porta explicitamente (não usar *middleware* mágico — a auditoria é regra de negócio, RNF03).

### RF21 — Notificação in-app ao Agente (Should)
- **Descrição:** ao validar/devolver/rejeitar, o sistema cria uma `Notificacao` para o agente autor, listável e marcável como lida.
- **Rastreabilidade:** A11; UC04 passo 9; entidade `Notificacao` do diagrama.
- **Hexagonal:** porta `PortaNotificacao`; adapter que persiste + publica via `PublicadorEventos`. Pode ser cortado sem afetar o fluxo ponta a ponta.

### RF22 — Evidências digitais (Should)
- **Descrição:** o Agente anexa arquivos (DEC-07) a uma ocorrência em `AGUARDANDO_REVISAO` ou `EM_CORRECAO`; cada evidência guarda `nome_original`, `formato`, `tamanho`, `hash_sha256`, `data_upload`; não pode ser removida, apenas marcada como "desconsiderada" com justificativa.
- **Rastreabilidade:** A12; RF01; UC01 passo 5 e exc. II; Planejamento S6; RNF03.
- **Hexagonal:** porta `ArmazenamentoArquivos.salvar(bytes, nome) -> chave`; adapter `ArmazenamentoDisco` (MVP) / S3 (futuro); `InterfaceAnexarEvidencia` → `AnexarEvidencia` → `RepositorioOcorrencia`, `ArmazenamentoArquivos`, `PortaAuditoria`.

### Resumo MoSCoW do MVP (revisado)

| Must | Should | Could (fora do MVP) |
| :--- | :--- | :--- |
| RF01*, RF04*, RF11, RF12, RF13, RF14, RF15, RF16, RF17, RF18, RF19, RF20 | RF21, RF22 | RF03, RF05–RF10 |

\* reescritos.

---

## 5. Requisitos não funcionais **reescritos e novos**

| ID | Requisito | Enunciado verificável (proposta) | Origem |
| :--- | :--- | :--- | :--- |
| **RNF01\*** | Desempenho e tempo real | Latência p95 < 1 s da ingestão de posição à atualização no painel, com ≥ 10 viaturas a 1 Hz e ≥ 5 painéis conectados, em rede local. `GET /v1/ocorrencias` (100 registros) p95 < 300 ms. | RNF-P01/02/03 |
| **RNF02\*** | Controle de acesso | JWT 8 h; senha argon2/bcrypt; papéis DEC-08; toda rota autenticada por padrão; CORS por lista de origens; tentativas negadas auditadas; HTTPS obrigatório fora de `development`. | RNF-P04/05/06 |
| **RNF03\*** | Imutabilidade e auditoria | Sem `DELETE` físico de ocorrência, envolvido, ordem, auditoria; sem cascatas de exclusão no ORM; `versao` + `atualizada_em` em agregados; `historico_status` append-only; tabela de auditoria sem UPDATE/DELETE para o *role* da aplicação. Nota de base legal LGPD art. 7º/11 (segurança pública). | RNF-P08–P12 |
| **RNF04\*** | Resiliência | Posição com idade > 60 s → viatura marcada `SEM_SINAL` no painel (amarelo) e excluída da sugestão automática; falha do mapa → tabela; WS reconecta com *backoff* 1/2/4/8 s (máx. 30 s); `/health` reporta `db: up/down`; integrações externas: 3 tentativas, *backoff* exponencial, depois log + status `Pendente`. | RNF-P13/14/15 |
| **RNF05\*** | Desacoplamento | `domain/` e `application/` não importam `fastapi`, `sqlalchemy`, `pydantic`, `jose`, `starlette`; verificado por `import-linter` no CI. Toda dependência externa do caso de uso entra por porta (ABC) injetada no *composition root*. | RNF-P16/17/18 |
| **RNF06** | Testabilidade | Cobertura ≥ 80 % em `domain/` + `application/` medida por `pytest-cov`; toda porta de saída tem *fake* em `tests/fakes/`; testes unitários não abrem rede nem disco; testes de integração rodam contra Postgres em Docker. | B1 |
| **RNF07** | Portabilidade / ambiente | `docker compose up` + `uv sync` + `alembic upgrade head` + `uv run uvicorn` sobem o sistema em máquina limpa em ≤ 10 min; nenhuma configuração fixa em código (tudo via `.env`); seed reproduzível por comando (`uv run python -m scripts.seed`). | B2, DIV-21/23 |
| **RNF08** | Internacionalização | Mensagens de erro da API e textos da UI em `pt` (padrão) e `en`, selecionados por `Accept-Language`/seletor; nenhuma string de usuário *hard-coded*; chaves ausentes caem em `pt`. | B3 (já implementado) |
| **RNF09** | Observabilidade | `/health` verifica conexão com o banco; logs JSON com `request_id`, `usuario_id`, `operacao`, `duracao_ms`; erros 5xx logados com *stack trace* e devolvidos com corpo padronizado `{detail, code, request_id}`. | B4 |
| **RNF10** | Privacidade / LGPD | CPF mascarado (`***.***.789-**`) em logs e em respostas para papéis ≠ Delegado/Agente autor; dados de seed são fictícios; documento de "base legal" mantido em `docs/`. | B5 |
| **RNF11** | Integridade transacional | Operações que alteram mais de um agregado (despacho, encerramento) executam em uma única transação via porta `UnidadeDeTrabalho`; *optimistic locking* por `versao` evita decisão dupla do Delegado. | B6 |
| **RNF12** | Contrato de API | OpenAPI gerado em `/docs` é a fonte de verdade dos DTOs; mudanças de contrato são versionadas em `/v1`; frontend gera tipos a partir do OpenAPI (ou os mantém sincronizados por revisão). | B7, Princípio 03 |

---

## 6. Lacunas de aderência hexagonal no código atual (HEX-nn)

| ID | Sev. | Lacuna | Onde | Correção sugerida |
| :--- | :---: | :--- | :--- | :--- |
| **HEX-01** | 🟠 | Adapter de entrada chama o repositório diretamente (sem caso de uso). | `ocorrencias_router.py:buscar_ocorrencia` | Criar `ObterDetalheOcorrencia` (RF13). |
| **HEX-02** | 🟠 | Injeção resolve a **implementação** (`OcorrenciaRepositorioSQLAlchemy`) e a composição está no router. | `ocorrencias_router.py:get_repositorio` | Mover *wiring* para `infrastructure/di.py` (ou `main.py`) e tipar dependências pela **porta** (`RepositorioOcorrencia`). Testes de adapter então trocam por `RepositorioOcorrenciaFake` via `app.dependency_overrides`. |
| **HEX-03** | 🟡 | Domínio lança `ValueError` genérico; handler global não o captura → 500. | `entity.py`, `main.py` | Criar `CampoObrigatorioError(DomainError)` / `ValorInvalidoError`; handler único para `DomainError` → 422 com chave i18n. |
| **HEX-04** | 🟠 | Máquina de estados do domínio diverge da documentada. | `entity.py:StatusOcorrencia` | Aplicar DEC-02. |
| **HEX-05** | 🔴 | Falta *value object* `Coordenada` e `data_hora_fato` na entidade. | `entity.py` | Aplicar DEC-03. |
| **HEX-06** | 🟡 | Invariante "≥ 1 envolvido" ausente. | `entity.py:__post_init__` / caso de uso | Validar no caso de uso `RegistrarOcorrenciaPolicial` **após** montar os envolvidos (a entidade precisa aceitar construção vazia para *rehydration* do repositório) — ou usar *factory* `Ocorrencia.registrar(...)` que valida e reserva `__init__` para o repositório. |
| **HEX-07** | 🟡 | `criada_em` usa `datetime.now()` dentro da entidade → não testável para regras temporais (60 s do GPS, "não futura"). | `entity.py` | Porta `Relogio.agora()`; caso de uso passa o instante para a entidade. |
| **HEX-08** | 🟡 | Protocolo gerado a partir de UUID dentro da entidade; formato diverge do diagrama (`long`). | `entity.py:_gerar_numero_protocolo` | Porta `GeradorProtocolo` (adapter: *sequence* Postgres `SGOPI-AAAA-NNNNNN`). A entidade recebe o protocolo pronto. |
| **HEX-09** | 🟡 | Transação (`commit`) dentro do repositório. Funciona para 1 agregado; quebra RNF11 no despacho. | `ocorrencia_repositorio_sqlalchemy.py:salvar` | Porta `UnidadeDeTrabalho` (context manager async) que detém a sessão; repositórios só fazem `add/merge`; o caso de uso faz `async with uow: ... await uow.commit()`. |
| **HEX-10** | 🟡 | Sem portas para auditoria, eventos, arquivos, token, hash, telemetria — todas previstas no diagrama de pacotes. | `application/ports/outbound/` | Criar as ABCs listadas nos RF11–RF22, cada uma com *fake* em `tests/fakes/`. |
| **HEX-11** | 🟡 | Sem Alembic; `create_all` no *startup*. | `main.py`, `migrations/` | `alembic init`, `env.py` async apontando para `Base.metadata`; remover `create_all` (manter apenas em testes de integração). |
| **HEX-12** | 🟡 | Cascatas de exclusão no ORM (contra RNF03). | `models.py` | Remover `cascade="all, delete-orphan"` / `ondelete="CASCADE"`; usar `passive_deletes=False` sem cascata. |
| **HEX-13** | ⚪ | Regra de ouro não verificada automaticamente. | — | `import-linter` com contrato `domain` ← nada externo; `application` ← só `domain`. |
| **HEX-14** | ⚪ | Frontend: `agente_policial_id` fixo; `buscarPorId` tipado errado; sem *hooks*/WS. | `RegistrarOcorrenciaPage.tsx`, `ocorrenciasService.ts` | Resolver com RF11 (token) e RF17 (WS). |

---

## 7. Estrutura-alvo do backend para o MVP (proposta)

```
backend/src/
├── domain/
│   ├── shared/
│   │   ├── exceptions.py        # DomainError, TransicaoInvalidaError, CampoObrigatorioError, ...
│   │   ├── geo.py               # Coordenada (VO) + calcular_distancia_km (Haversine)
│   │   └── eventos.py           # EventoDominio base
│   ├── ocorrencia/
│   │   ├── entity.py            # Ocorrencia, Envolvido, TipificacaoPenal, Evidencia
│   │   ├── status.py            # StatusOcorrencia + tabela de transições (DEC-02)
│   │   └── eventos.py           # OcorrenciaValidada, OcorrenciaDespachada, ...
│   ├── viatura/entity.py        # Viatura, SituacaoViatura, Posicao
│   ├── despacho/entity.py       # OrdemDeDespacho
│   ├── usuario/entity.py        # Usuario, Papel
│   └── auditoria/entity.py      # RegistroAuditoria
├── application/
│   ├── ports/
│   │   ├── inbound/             # Interface* + DTOs (um arquivo por UC)
│   │   └── outbound/            # Repositorio*, PortaAuditoria, PublicadorEventos, Relogio,
│   │                            # GeradorProtocolo, UnidadeDeTrabalho, HasherSenha,
│   │                            # ProvedorToken, ArmazenamentoArquivos, PortaNotificacao
│   └── use_cases/
│       ├── auth/                # AutenticarUsuario
│       ├── ocorrencia/          # Registrar, Listar, ObterDetalhe, Validar, DevolverParaCorrecao,
│       │                        # Rejeitar, Corrigir, Reenviar, Encerrar, AnexarEvidencia
│       ├── viatura/             # Cadastrar, AlterarSituacao, Listar, RegistrarPosicao
│       └── despacho/            # SugerirViaturasProximas, DespacharViatura
├── adapters/
│   ├── inbound/
│   │   ├── http/v1/             # auth_router, ocorrencias_router, viaturas_router,
│   │   │                        # despacho_router, telemetria_router, auditoria_router
│   │   ├── http/deps.py         # usuario_atual(), exigir_papel()
│   │   ├── websocket/           # tempo_real_router + GerenciadorConexoes
│   │   └── simulador/           # SimuladorTelemetria (driving adapter)
│   └── outbound/
│       ├── persistence/         # *RepositorioSQLAlchemy, UnidadeDeTrabalhoSQLAlchemy,
│       │                        # AuditoriaSQLAlchemy, GeradorProtocoloPostgres
│       ├── eventos/             # PublicadorEventosEmMemoria
│       ├── seguranca/           # HasherArgon2, ProvedorTokenJose
│       ├── arquivos/            # ArmazenamentoDisco
│       └── relogio/             # RelogioSistema
├── infrastructure/
│   ├── config/settings.py
│   ├── database/{connection,models}.py + migrations/ (Alembic)
│   ├── i18n/
│   ├── logging.py               # JSON + request_id
│   └── di.py                    # composition root: monta casos de uso a partir dos adapters
└── main.py                      # cria app, registra routers, handlers, lifespan
```

Regras de dependência (verificáveis por `import-linter`): `domain` ← nada; `application` ← `domain`; `adapters` ← `application`, `domain`, `infrastructure`; `infrastructure` ← `domain` (só para models espelharem enums), nunca o contrário.

---

## O que foi feito nesta etapa

1. Fechadas **9 decisões de base** (DEC-01…DEC-09) que resolvem as divergências bloqueantes da Etapa 1.
2. Proposta a **máquina de estados unificada** da ocorrência (6 estados, 7 transições, papéis por transição) e a da viatura.
3. **Reescritos** RF01, RF02 (guarda-chuva) e RF04 com critérios de aceite verificáveis.
4. **Criados RF11–RF22** (12 requisitos), cada um com rastreabilidade, critérios de aceite, MoSCoW e mapeamento em porta de entrada → caso de uso → portas de saída → adapters.
5. **Reescritos RNF01–RNF05** de forma mensurável e **criados RNF06–RNF12**.
6. Catalogadas **14 lacunas de aderência hexagonal** no código atual (HEX-01…HEX-14) com correção sugerida.
7. Proposta a estrutura-alvo de diretórios do backend para o MVP.
8. Nenhum documento original nem código alterado — tudo permanece como proposta.

**Próxima etapa:** consolidar o que foi encontrado, o que ficou fora do escopo e a ordem recomendada das próximas implementações (`ETAPA-05`).
