# 🗳️ Ata de Decisões Técnicas — SGOPI Sentinela

**Projeto:** SGOPI Sentinela · **Data de ratificação:** 14/09/2026
**Origem:** `NEXT-00` da [ETAPA-05](ETAPA-05-consolidacao-escopo-e-proximos-passos.md); decisões propostas na [ETAPA-04 §1](ETAPA-04-novos-requisitos-mvp-hexagonal.md).

Este documento é a **fonte de verdade** sobre *por que* o código é como é. Toda divergência entre o código e a documentação original (wiki, `DOCUMENTACAO_DE_ENGENHARIA.md`, diagramas UML) deve estar explicada por uma decisão registrada aqui. Se não estiver, é bug de um dos dois lados.

**Como ler:** `DEC-01`…`DEC-09` foram propostas na Etapa 4 e estão **ratificadas e implementadas**. `DEC-10`…`DEC-15` são decisões que foram **tomadas durante a implementação sem registro prévio** e estão sendo formalizadas agora — foram identificadas na auditoria de conformidade de 14/09/2026.

---

## 1. Decisões ratificadas (propostas na Etapa 4)

| ID | Decisão | Resolve | Estado | Evidência no código |
| :--- | :--- | :--- | :---: | :--- |
| **DEC-01** | **Persistência = PostgreSQL 16 + SQLAlchemy 2 async + Alembic.** Firestore/Firebase e JPA/Hibernate/STOMP/SockJS são resquícios da concepção Java/Spring e não valem. | DIV-01, DIV-02 | ✅ | `infrastructure/database/`, 3 migrations Alembic |
| **DEC-02** | **Máquina de estados única da ocorrência:** 6 estados, 6 transições (§2). | DIV-03/04/05 | ✅ | `domain/ocorrencia/status.py` |
| **DEC-03** | **Coordenada geográfica obrigatória** na ocorrência (VO `Coordenada`) + `data_hora_fato`. Geocodificação de endereço fica como porta futura. | DIV-16 | ✅ | `domain/shared/geo.py`, `ocorrencias.latitude/longitude` |
| **DEC-04** | **Envolvido permanece 1:N com a ocorrência no MVP** (não é pessoa reutilizável). Campos: `nome`, `tipo`, `documento` (CPF opcional, validado se presente). Ver §3 para a estratégia de mapeamento da generalização. | DIV-17 | ✅ | `domain/ocorrencia/entity.py:Envolvido` |
| **DEC-05** | **Distância = Haversine** sobre a última posição válida com idade ≤ 60 s (parametrizável). | DIV-07 | ✅ | `domain/despacho/servico_proximidade.py` |
| **DEC-06** | **Tempo real = WebSocket nativo do FastAPI**; eventos internos via porta `PublicadorEventos` com adapter em memória. Broker é evolução pós-MVP. | RNF-P02 | ✅ | `adapters/inbound/websocket/`, `adapters/outbound/eventos/` |
| **DEC-07** | **Evidências no MVP:** `pdf, jpg, jpeg, png`, ≤ 10 MB/arquivo, ≤ 10 arquivos/ocorrência, em disco local atrás da porta `ArmazenamentoArquivos`; integridade por SHA-256 e download somente após conferência autorizada. | DIV-08 | ✅ | `application/ports/outbound/armazenamento_arquivos.py`; `adapters/outbound/arquivos/armazenamento_disco.py`; `application/use_cases/ocorrencia/acessar_evidencia.py`; endpoints no `ocorrencias_router.py`; testes unitários, de adapter e HTTP |
| **DEC-08** | **Papéis do MVP:** `AGENTE`, `DELEGADO`, `OPERADOR_CENTRAL`. `SUPERVISOR`, `PERITO`, `ESCRIVAO` ficam no enum sem UC. Não há acesso anônimo. Ver §3. | DIV-06 | ✅ | `domain/usuario/entity.py:Papel` |
| **DEC-09** | **Sem assinatura digital, PDF ou ICP-Brasil no MVP.** "Validação" = transição de estado + `validada_por_id` + auditoria + hash SHA-256 da narrativa. | RF-P18, RF-P20 | ✅ | `Ocorrencia.calcular_hash_narrativa()` |

---

## 2. Máquina de estados ratificada (DEC-02)

```
                 ┌──────────────────────────────────────────────┐
                 │                          reenviar (Agente)   │
                 ▼                                              │
 [criar] ─► AGUARDANDO_REVISAO ──validar (Delegado)──► VALIDADA ──despachar (Operador)──► EM_ATENDIMENTO ──encerrar──► ENCERRADA
                 │                                                                                (Operador/Delegado)
                 ├──devolver_para_correcao (Delegado, justificativa ≥ 10 car.)──► EM_CORRECAO ──┘
                 │
                 └──rejeitar (Delegado, justificativa ≥ 10 car.)──► REJEITADA  (terminal)
```

Pontos que **substituem** o que está nos diagramas e na wiki:

- `VALIDADA` absorve o estado **`Aguardando Atendimento`** do diagrama de classes — não existem dois estados.
- **`REJEITADA` existe e é terminal.** Não aparece no enum do diagrama de classes.
- Não existem `Rascunho`, `Em Despacho` nem `Concluída` (§3.2 do documento de engenharia), nem `REGISTRADA`/`EM_VALIDACAO` (código antigo), nem `FINALIZADA` (wiki §22).
- Estado inicial é **compulsório**: `AGUARDANDO_REVISAO`. Não há transição `enviar_para_validacao`.

### Máquina de estados da Viatura

```
INDISPONIVEL ⇄ DISPONIVEL ──despachar──► EM_DESLOCAMENTO ──chegar_ao_local──► OPERANDO
                    ▲                          │                                 │
                    └──────────liberar─────────┴─────────────────────────────────┘
```

> ⚠️ **Simplificação ativa no MVP:** `chegar_ao_local()` existe em `domain/viatura/entity.py` mas **nenhum caso de uso o expõe**. `AlterarSituacaoViatura` só aceita `DISPONIVEL`/`INDISPONIVEL` manualmente, e `EncerrarOcorrencia` chama `liberar()` direto. Na prática o ciclo executável é `DISPONIVEL → EM_DESLOCAMENTO → DISPONIVEL`, e **`OPERANDO` é inalcançável pela API**. Era a simplificação prevista na Etapa 4 §2. Decidir antes da apresentação: expor a transição ou remover `OPERANDO` do enum.

---

## 3. Estratégia de mapeamento das generalizações

As duas hierarquias do diagrama de classes foram mapeadas por **tabela única com coluna discriminadora** (*single-table inheritance*), não por tabela-por-subtipo. Esta é uma das três estratégias canônicas de mapeamento de generalização UML→relacional; a escolha é deliberada e está justificada abaixo.

### 3.1 `Usuario` → `Delegado` / `AgentePolicial` / `OperadorCentral` / `Supervisor` / `PeritoCriminal`

**Decisão: coluna discriminadora `usuarios.papel` + enum `Papel`. Permanente — não é dívida técnica.**

1. **Nenhum atributo de subtipo é lido por caso de uso.** `turno`, `gradHierarquica`, `numeroDistintivo`, `comarcaAtuacao`, `matriculaFuncional`, `assinaturaDigital` não têm consumidor no MVP nem nos *Should Have*. `assinaturaDigital` depende de RF07/RF08, excluídos por DEC-09.
2. **Tabelas por subtipo quebrariam a trilha de auditoria em mudança de papel.** No mapeamento relacional original, `Delegado` tem PK própria (`codigoDelegado`) e `Ocorrencia.codigoDelegado` aponta para ela. Um agente promovido a delegado exigiria uma linha nova, com PK nova, em outra tabela — e as ocorrências que ele registrou como agente continuariam apontando para a identidade antiga. Com a coluna discriminadora é um `UPDATE`, e `ocorrencias.agente_policial_id`, `ocorrencias.validada_por_id`, `ordens_despacho.operador_id` e `registros_auditoria.quem` continuam apontando para a **mesma pessoa**. O RNF03* exige histórico inalterável; a herança o tornaria frágil.
3. **A RBAC fica mais simples.** `exigir_papel(Papel.DELEGADO)` é uma comparação de enum (`adapters/inbound/http/deps.py`). Com subclasses viraria *downcast*/`isinstance` em cada rota.
4. A restrição do diagrama é `{disjoint, incomplete}` — exatamente a semântica de uma coluna discriminadora. **O enum não contradiz o diagrama; é um mapeamento válido dele.**

### 3.2 `Envolvido` → `Suspeito` / `Vitima` / `Testemunha`

**Decisão: coluna discriminadora `envolvidos.tipo` + enum `TipoEnvolvido` no MVP. É dívida técnica consciente (E7), com ordem de pagamento definida.**

1. Os atributos dos subtipos **são** de requisito real (`Suspeito.reincidente` e `quantidadePassagens` são o RF05; `Vitima.necessitaAtendimento` é triagem), mas nenhum deles é calculável hoje: `reincidente` é propriedade derivada **de várias ocorrências**, e o modelo é 1:N — cada linha de `envolvidos` pertence a uma única ocorrência e não há unicidade em `documento`.
2. **O pré-requisito de RF05/RF06 é a pessoa reutilizável (N:N), não os subtipos.** Criar `Suspeito` antes disso produz um campo que não se consegue preencher corretamente. Ordem de pagamento da dívida: **(1) `Pessoa` reutilizável + `EnvolvidoOcorrencia` N:N → (2) atributos de subtipo.** Nunca o inverso.
3. Quando for feito, preferir **composição / objetos-papel** a herança de classe: a restrição do diagrama é `{overlapping}`, e sobreposição não mapeia bem em nenhuma das três estratégias relacionais nem em hierarquia de classes.

**Correção de semântica exigida no diagrama:** a generalização está marcada `{overlapping, complete}` — a mesma pessoa podendo ser vítima **e** testemunha. Uma coluna `tipo` única é **disjoint**, o oposto. Hoje o sistema não quebra (o agente cadastra duas linhas para a mesma pessoa, e nada impede), mas o diagrama afirma algo que o código não sustenta.

**Resolução adotada:** reinterpretar a generalização como incidindo sobre a **qualificação do envolvido naquela ocorrência**, não sobre a *pessoa*. Sob essa leitura o modelo é `{disjoint, complete}` e passa a estar correto — cada linha é um papel exercido, e uma pessoa com dois papéis tem duas qualificações. Custa uma anotação no diagrama em vez de tocar entidade, DTO, schema, migration, repositório, formulário e função de hash com o escopo congelado.

---

## 4. Decisões formalizadas retroativamente

Tomadas durante a implementação, sem registro prévio. Cada uma contradiz um diagrama e precisa ser refletida neles (NEXT-18).

| ID | Decisão | Contradiz | Justificativa |
| :--- | :--- | :--- | :--- |
| **DEC-10** | **Chave primária = `UUID` (v4) em todas as tabelas**, gerada na aplicação. | Mapeamento relacional (`codigoX: bigint` em 28 tabelas) | ID gerado no domínio antes de tocar o banco — a entidade nasce válida e identificável sem *round-trip*, o que os testes com *fake* de repositório exigem. Evita enumeração de recursos na API (RNF02*). Custo: 16 B vs 8 B por chave, irrelevante na escala do MVP. |
| **DEC-11** | **`numero_protocolo` é `String(50)` no formato `SGOPI-AAAA-NNNNNN`**, com contador por ano em `sequencias_protocolo`. | Diagrama de classes (`/numeroProtocolo: long`) e relacional (`bigint`) | Protocolo é identificador **de negócio**, lido e ditado por humanos, e precisa carregar o ano. Gerado pela porta `GeradorProtocolo` (HEX-08), não pelo banco. Mesma decisão vale para `ordens_despacho.numero` (`OD-AAAA-NNNNNN`). |
| **DEC-12** | **`OrdemDeServico` → `OrdemDeDespacho`, com cardinalidade 1 ordem : 1 viatura.** | Diagrama de classes e relacional (`OrdemDeServicoViatura` N:N) | O nome reflete o UC02 (despacho tático), e "ordem de serviço" colidia com o vocabulário administrativo. A N:N era para despacho de múltiplas viaturas num mesmo evento; no MVP, duas viaturas na mesma ocorrência = duas ordens, o que preserva rastreabilidade individual por viatura. Reavaliar se o pós-MVP exigir despacho em bloco. |
| **DEC-13** | **Telemetria GPS é adaptador de ENTRADA, não porta de saída.** `SimuladorTelemetria` empurra posições via `POST /v1/telemetria/posicoes`. | Diagrama de pacotes (`InterfaceSinalGPS` em *Portas de Saída*) | O sistema não *consulta* GPS; recebe telemetria. Modelar como porta de saída implicaria *polling* do núcleo para fora, invertendo o fluxo real e impedindo o simulador de ser ligado/desligado como *driving adapter*. Previsto em NEXT-12. |
| **DEC-14** | **Sem PostGIS.** Coordenadas como duas colunas `Float`; distância por Haversine em serviço de domínio puro. | Wiki §20 (PostgreSQL + PostGIS), Wiki §26 ("utilizar os recursos geográficos do banco") | Proximidade é **regra de negócio** (DEC-05). Colocá-la numa consulta SQL a tiraria do domínio e a tornaria não testável sem banco, violando o RNF05* e a regra de ouro verificada por `import-linter`. Reavaliar quando o volume exigir índice espacial (RF05, manchas criminais). |
| **DEC-15** | **`TipificacaoPenal` é entidade própria** (`artigo`, `descricao`), 0..* por ocorrência, em tabela separada. | Diagrama de classes (`Ocorrencia.tipoCrime: String`) | Uma ocorrência tem frequentemente mais de um enquadramento legal. `Ocorrencia.natureza` permanece como classificação operacional livre; a tipificação é a jurídica. |

### 4.1 Colunas transversais sem equivalente nos diagramas

Consequências diretas de RNF03* e RNF11, presentes em várias tabelas e ausentes de todos os diagramas:

- **`versao: int`** — *optimistic locking* verificado pelo repositório (`SELECT … FOR UPDATE` + comparação).
- **`ativo: bool`** — *soft delete*. Nenhuma cascata de exclusão existe no esquema; filhos removidos do agregado são marcados inativos.
- **`historico_status_ocorrencia`** e **`registros_auditoria`** — *append-only*, com trigger no PostgreSQL (migration `0001`).

---

## 5. Rastreabilidade das decisões para os diagramas

| Diagrama | Decisões que o afetam | Ação |
| :--- | :--- | :--- |
| Classes de domínio | DEC-02, 03, 04, 08, 11, 12, 15 + §4.1 | Novo diagrama "modelo implementado" + anotações no conceitual |
| Mapeamento relacional | DEC-04, 08, 10, 11, 12, 14, 15 + §4.1 | Novo diagrama "esquema do MVP" (10 tabelas) |
| Pacotes (hexagonal) | DEC-06, 13, 14 | Edição no lugar |
| Casos de uso | DEC-08 | Ajustar atores aos 3 papéis do MVP |
| Implantação | DEC-01, 06 | Remover `.jar` / `.xml` / STOMP / SockJS |

Checklist executável: [`NEXT-18-ajustes-nos-diagramas.md`](NEXT-18-ajustes-nos-diagramas.md).

---

## 6. Decisões em aberto

| # | Questão | Prazo | Quem decide |
| :--- | :--- | :--- | :--- |
| A1 | Expor `chegar_ao_local()` (EM_DESLOCAMENTO → OPERANDO) ou remover `OPERANDO` do enum? | Antes da apresentação | Equipe |
| A2 | RF21 (notificação in-app) entra na Sprint 5 ou fica pós-MVP? RF22 foi concluído na issue #41. | Sprint 5 | Equipe |
| A3 | Reavaliar DEC-12 (N:N ordem↔viatura) se o pós-MVP exigir despacho em bloco | Pós-MVP | Equipe |
| A4 | Reavaliar DEC-14 (PostGIS) ao iniciar RF05 (manchas criminais) | Pós-MVP | Equipe |

---

## Histórico de revisões

| Data | O que mudou |
| :--- | :--- |
| 14/09/2026 | Criação. Ratificação de DEC-01…DEC-09, formalização de DEC-10…DEC-15, registro da estratégia de mapeamento das generalizações (§3) e das quatro decisões em aberto. |
| 19/09/2026 | DEC-07 atualizada após a conclusão de RF22 na issue #41; A2 mantida aberta somente para RF21. |
