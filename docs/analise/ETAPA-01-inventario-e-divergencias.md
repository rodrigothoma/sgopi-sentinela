# ETAPA 01 — Inventário da documentação e catálogo de divergências

**Objetivo da etapa:** ler todos os artefatos, registrar o que existe e cruzar documento × documento e documento × código, antes de julgar os requisitos. Sem esta base, a análise de requisitos (Etapas 2 e 3) poderia tratar como "problema de requisito" algo que é apenas documentação desatualizada.

---

## 1. Inventário do que existe

### 1.1 Documentação

| Artefato | Estado | Observação |
| :--- | :--- | :--- |
| `README.md` | Atualizado com o layout monorepo e comandos de execução | Referencia `frontend/src/hooks/` que não existe; promete cliente WebSocket em `services/` que não existe |
| `DOCUMENTACAO_DE_ENGENHARIA.md` | Completo (RF01–RF10, RNF01–RNF05, MoSCoW, MVP, arquitetura, 12 UCs) | Traz resquícios da concepção original em **Java/Spring** e menciona **Firebase Firestore** (§4.3) |
| `PLANEJAMENTO_DESENVOLVIMENTO.md` | Sprints 2–5 com tarefas por pessoa | Parágrafo "Estado atual do código" (Sprint 2) está **desatualizado** |
| Diagrama de casos de uso | 11 casos de uso, 6 atores | Falta UC12; ator de UC10 diverge do texto |
| Diagrama de classes de domínio | 28 classes/enums | Modelo rico, mas com métodos de consulta/repositório dentro das entidades |
| Diagrama de pacotes (hexagonal) | Portas de entrada/saída, casos de uso, entidades, adaptadores, DAOs | Coerente com hexagonal; nomes em PT-BR |
| Componentes (módulos hexagonal / executável) | Agrupamento em 4 módulos: OcorrênciasEInquéritos, TáticaEInteligência, PortalCidadão, Perícia | Bom para definir *bounded contexts* |
| Implantação | 4 nós (Cliente, Anúbis, Rá, Seth, Thoth) | Contém `Scheduler.jar` e `Autenticacao.xml` (artefatos Java) |
| Mapeamento relacional | ~25 tabelas | Consistente com o diagrama de classes; **não** com o código |
| Sequência sq01–sq11 | Padrão BCE (boundary/control/entity) | Nenhum diagrama mostra porta, caso de uso ou repositório |

### 1.2 Código (branch `matheus-Fastapi`)

| Camada | O que existe | Cobertura de UC |
| :--- | :--- | :--- |
| `domain/ocorrencia/entity.py` | `Ocorrencia`, `Envolvido`, `TipificacaoPenal`, enums `StatusOcorrencia` (4 estados) e `TipoEnvolvido`; transições `enviar_para_validacao`, `validar`, `rejeitar` | UC01 parcial; UC04 parcial (só domínio) |
| `application/ports/inbound` | `InterfaceRegistrarOcorrenciaPolicial` + DTOs | UC01 |
| `application/ports/outbound` | `RepositorioOcorrencia` (`salvar`, `buscar_por_id`, `listar`) | UC01 |
| `application/use_cases` | `RegistrarOcorrenciaPolicial` | UC01 |
| `adapters/inbound/http/v1` | `POST /v1/ocorrencias/`, `GET /v1/ocorrencias/{id}` | UC01 + detalhe |
| `adapters/outbound/persistence` | `OcorrenciaRepositorioSQLAlchemy` | UC01 |
| `infrastructure` | settings (pydantic-settings), engine async, models (3 tabelas), i18n pt/en, `create_all` no startup | — |
| `tests` | 15 testes unitários (entidade + caso de uso com fake) — **todos passam** | UC01 |
| `frontend` | `RegistrarOcorrenciaPage` com sub-forms de envolvido e tipificação; i18n pt/en; axios | UC01 |

---

## 2. Catálogo de divergências

Legenda de severidade: 🔴 bloqueante · 🟠 alto · 🟡 médio · ⚪ baixo

### 2.1 Documento × Documento

| ID | Sev. | Onde | Divergência | Impacto |
| :--- | :---: | :--- | :--- | :--- |
| **DIV-01** | 🔴 | Doc §4.3 × README × Doc §5.6 × código | §4.3 declara **Firebase Cloud Firestore (NoSQL) + Firebase Admin SDK** como persistência. README, §5.6 (mapeamento relacional) e o código usam **PostgreSQL + SQLAlchemy + Alembic**. | Duas estratégias de persistência incompatíveis no mesmo documento. A que vale é PostgreSQL; §4.3 precisa ser reescrita. |
| **DIV-02** | 🟠 | Doc §4.2 (diagrama ASCII), §4.3, diagrama de implantação | Resquícios de stack Java/Spring: "JPA / Hibernate", "WebSockets (STOMP/SockJS)", `Scheduler.jar`, `Autenticacao.xml`. | Confunde leitor; STOMP/SockJS não é a tecnologia de WebSocket do FastAPI. |
| **DIV-03** | 🔴 | Doc §3.2 × diagrama de classes (enum `Status`) × UC02/UC04 × código | **Quatro máquinas de estado diferentes** para a ocorrência:<br>• §3.2: `Rascunho → Aguardando Revisão → Validada / Rejeitada → Em Despacho → Concluída`<br>• Enum do diagrama: `Aguardando Revisao, Validada, Em Correcao, Encerrada, Aguardando Atendimento, Em Atendimento`<br>• UC04: `Validada` ou `Rejeitada / Em Correção`; UC02: `Em Atendimento`<br>• Código: `REGISTRADA, EM_VALIDACAO, VALIDADA, REJEITADA` | Bloqueia a Sprint 3 (S4 "transições no domínio") e a Sprint 4 (D6). Sem uma máquina de estados única, cada integrante implementará uma diferente. |
| **DIV-04** | 🟠 | UC01 regra 3 × sq04 × código | UC01 diz que toda ocorrência nasce **compulsoriamente** em `Aguardando Revisão`. O código nasce em `REGISTRADA` e exige `enviar_para_validacao()` — transição que não existe em nenhum documento. | Regra de negócio documentada não é a implementada. |
| **DIV-05** | 🟡 | Doc §1.1 RF04 × UC04 × sq04 | RF04 fala em "solicitar correções ou validar" (2 saídas). UC04 fala em `Validada` ou `Rejeitada / Em Correção` (3 saídas, sem definir se `Rejeitada` é terminal). sq04 só modela `Validada` e `EmCorrecao`. | Semântica de "Rejeitada" indefinida. |
| **DIV-06** | 🟡 | Diagrama de casos de uso × texto | (a) UC10 no diagrama tem ator **Operador da Central**; no texto, **Agente/Delegado Requisitante**. (b) **UC12** existe no texto, não no diagrama. (c) UC07 tem Delegado como ator principal no texto; no diagrama só Perito. (d) Atores **Escrivão** (UC06) e **Analista de Inteligência** (UC05) aparecem no texto, não no diagrama nem na lista de papéis do RNF02. | Lista de papéis do RBAC (RNF02) incompleta. |
| **DIV-07** | 🟡 | Doc §3.2 × UC02 × Planejamento D5 | Cálculo de proximidade: "euclidiano / Haversine" (§3.2), "distância geodésica" (UC02), "Haversine no domínio" (D5). | Deve fixar um: Haversine. |
| **DIV-08** | 🟡 | UC01 exceção II × sq01 × §3.2 | Formatos aceitos: UC01 diz `.pdf, .jpg, .png`; sq01 diz `.jpg, .pdf, .mp4`; §3.2 exclui vídeo do MVP. | Definir a lista única. |
| **DIV-09** | 🟡 | Doc §7.1/README × Planejamento F3 | Meta de cobertura ≥ 80% aparece como estratégia, mas **não é RNF** e não há `pytest-cov` configurado. | Meta não verificável hoje. |
| **DIV-10** | ⚪ | Doc cabeçalho | "Semestre Letivo: 2026/1" com calendário de setembro/outubro (2026/2). | Editorial. |
| **DIV-11** | 🟡 | Diagramas de sequência × diagrama de pacotes | Sequências seguem **BCE**: o `Controle…` cria entidades e chama métodos delas diretamente; não aparecem **portas, casos de uso nem repositórios**. sq01 sequer mostra persistência. sq04 não mostra a checagem de papel (regra 1 do UC04). | Os diagramas comportamentais não refletem a arquitetura declarada; servem como fluxo de UI, não como guia de implementação hexagonal. |
| **DIV-12** | 🟠 | Diagrama de classes | `Ocorrencia` concentra métodos de consulta/repositório (`listarOcorrencias`, `consultarOcorrencia(long)`, `buscarConexoes`, `listarInqueritosComPericiaEmAberto`…). O mesmo ocorre em `MedidaProtetiva`, `ComunicacaoInteragencias`, `Viatura`. | Em hexagonal, consultas são **portas de saída** e orquestração é **caso de uso**. Se o diagrama for seguido ao pé da letra, o domínio dependerá de I/O. |
| **DIV-13** | 🟡 | UC04 passo 2 × diagrama de classes | UC04 ordena a fila "por antiguidade **e gravidade**". Nenhuma classe possui atributo de gravidade/prioridade da ocorrência (só `Alerta.prioridade`). | Ordenação por gravidade não é implementável. |
| **DIV-14** | 🟡 | RF08 × diagrama de classes | RF08 valida "documentos emitidos", mas **não existe RF/UC de emissão** de documento (BO/certidão em PDF). `DocumentoPolicial` e `ComprovanteAutenticacao` existem só no diagrama. | RF08 depende de funcionalidade não especificada. |
| **DIV-15** | 🟡 | UC06 pré-condição × RFs | "O inquérito deve estar formalmente aberto no sistema", mas não há RF/UC para abrir inquérito. | Mesmo padrão de DIV-14. |

### 2.2 Documento × Código

| ID | Sev. | Onde | Divergência | Impacto |
| :--- | :---: | :--- | :--- | :--- |
| **DIV-16** | 🔴 | Diagrama de classes/relacional × `entity.py` | `Ocorrencia` no diagrama tem `dataHoraFato`, `latitude`, `longitude`, `local`, `tipoCrime`, `chaveSeguranca`. O código tem `natureza`, `descricao`, `localizacao` (string livre) e **nenhuma coordenada**. | **Sem latitude/longitude não existe RF02 (proximidade), RF05 (manchas) nem mapa tático.** Bloqueia a Sprint 4 inteira. |
| **DIV-17** | 🟠 | Diagrama × `entity.py` | `Envolvido` no diagrama: `cpf, nome, dataNascimento, endereco, telefone` + subtipos com atributos próprios (`Vitima.estadoFisico/necessitaAtendimento`, `Suspeito.quantidadePassagens/reincidente`, `Testemunha.tipoDepoimento`), generalização *overlapping/complete*. Código: `nome, tipo, documento`. Relacional: N:N `EnvolvidoOcorrencia`; código: 1:N (envolvido pertence a uma única ocorrência). | Reincidência (RF05) e suspeitos em comum (RF06) exigem identificar a **mesma pessoa** em várias ocorrências — impossível no modelo 1:N sem chave natural. Não bloqueia o MVP, mas a decisão deve ser consciente. |
| **DIV-18** | 🟠 | UC01 regra 1 × código × frontend | "Qualificação de **no mínimo um envolvido** é obrigatória". Código e frontend aceitam zero envolvidos (há teste que registra sem nenhum). | Regra de negócio documentada não implementada. |
| **DIV-19** | 🟠 | RF01/UC01 passo 5 × código | Evidências digitais (upload) não existem no domínio, na API nem no frontend. Planejamento posiciona em S6. | OK como planejamento, mas o RF01 hoje é atendido parcialmente. |
| **DIV-20** | 🟠 | UC01 pré-condição × código × frontend | Autenticação é pré-condição de todos os UCs. Não há login; `agente_policial_id` vem no body (TODO no router) e o frontend envia UUID fixo `00000000-…-000000000001`. `python-jose` e `JWT_SECRET_KEY` existem, mas nada os usa. | Esperado para Sprint 2; bloqueia critério de aceite 2 do §3.4 ("somente Delegado valida"). |
| **DIV-21** | 🟠 | README/Doc/Planejamento T4 × código | Documentação promete **Alembic**; código usa `Base.metadata.create_all` no `lifespan`; `migrations/` só tem `.gitkeep`, sem `alembic.ini`. | Toda mudança de esquema (lat/long, viaturas, usuários) exigirá recriar o banco. |
| **DIV-22** | 🟡 | Planejamento T1 × `main.py` | T1 pede `/health` "verificando a conexão com o banco"; o endpoint só responde `{"status": "ok"}`. | Verificação 1 não é provável como descrita. |
| **DIV-23** | 🟡 | `docker-compose.yml` × `main.py` | `seed.sql` é montado em `docker-entrypoint-initdb.d` (roda na **criação do volume**), mas as tabelas são criadas pela aplicação **depois**. Qualquer `INSERT` no seed falhará. | F4 (seed de demo) precisa de outra estratégia. |
| **DIV-24** | 🟡 | RNF03 × `models.py` | RNF03 exige imutabilidade e proíbe exclusão. Models têm `cascade="all, delete-orphan"` e `ondelete="CASCADE"`. | Esquema físico permite o que o RNF proíbe. |
| **DIV-25** | 🟡 | RNF02 × `main.py` | CORS com `allow_origins=["*"]` **e** `allow_credentials=True` — combinação inválida pela spec (navegadores rejeitam credenciais com wildcard) e insegura. | Vai quebrar no momento em que houver cookie/Authorization com credentials. |
| **DIV-26** | 🟡 | Planejamento Sprint 2 × código | "Estado atual do código: só existe a entidade `domain/ocorrencia.py`" — desatualizado; a fatia vertical T2–T6 já está no repositório. | Planejamento precisa de *check* das tarefas concluídas. |
| **DIV-27** | 🟡 | Doc §4.1 × código | §4.1 cita `domain/entities` e `application/usecases`; código usa `domain/<contexto>/entity.py` e `application/use_cases/`. | Nomenclatura. |
| **DIV-28** | 🟡 | `entity.py` × `exceptions.py` × `main.py` | Domínio lança `ValueError` para campo obrigatório; só `EntidadeNaoEncontradaError` e `TransicaoInvalidaError` têm handler. Chaves i18n `descricao_vazia`/`localizacao_vazia` existem e não são usadas. | `POST` com descrição vazia devolve **500** em vez de 422. |
| **DIV-29** | 🟡 | Hexagonal × `ocorrencias_router.py` | `GET /{id}` chama o repositório **direto do adapter**, sem caso de uso; `Depends` resolve a implementação concreta `OcorrenciaRepositorioSQLAlchemy` (não a porta); a composição está no router e não no *composition root* (`main.py`). | Viola a regra "adapter → porta de entrada → caso de uso → porta de saída". Detalhado em HEX-nn na Etapa 4. |
| **DIV-30** | ⚪ | README × frontend | README lista `hooks/` e "Clients HTTP e WebSocket"; frontend não tem `hooks/` nem WebSocket. `ocorrenciasService.buscarPorId` tipa a resposta como `OcorrenciaResponse`, mas a API devolve o detalhe (com envolvidos/tipificações). | Cosmético/tipagem. |
| **DIV-31** | ⚪ | Doc §7.2 × git | §7.2 prevê `main` e `dev`; existe `origin/dev`, mas os commits recentes estão em branches pessoais. Compatível com o Princípio 01 do planejamento, só falta registrar. | Editorial. |

---

## 3. Síntese da etapa

- **3 divergências bloqueantes** para o MVP: stack de persistência (DIV-01), máquina de estados (DIV-03) e ausência de coordenadas geográficas (DIV-16).
- **A raiz da maioria dos problemas** é a migração de uma modelagem concebida em Java/Spring para Python/FastAPI sem revisão sistemática do documento — e a fatia vertical de código ter sido escrita a partir do README, não do diagrama de classes.
- Os diagramas de sequência são úteis para o frontend, mas **não podem ser usados como especificação da camada de aplicação** (DIV-11).

---

## O que foi feito nesta etapa

1. Lidos integralmente `README.md`, `DOCUMENTACAO_DE_ENGENHARIA.md` e `PLANEJAMENTO_DESENVOLVIMENTO.md`.
2. Lidos visualmente 7 diagramas estruturais e os 3 diagramas de sequência do escopo do MVP (sq01, sq02, sq04).
3. Lido todo o código do backend (`src/` e `tests/`) e do frontend (`src/`), além de `pyproject.toml`, `.env.example`, `seed.sql`, `docker-compose.yml`.
4. Executados os testes unitários do backend (`uv run pytest`): **15 passed**.
5. Produzido o inventário (§1) e o catálogo de **31 divergências** (§2), cada uma com severidade e impacto.
6. **Nenhum arquivo original foi alterado.**

**Próxima etapa:** analisar RF01–RF10 e UC01–UC12 individualmente (`ETAPA-02`).
