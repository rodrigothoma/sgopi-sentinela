# ETAPA 02 — Análise dos Requisitos Funcionais (RF01–RF10) e Casos de Uso (UC01–UC12)

**Objetivo da etapa:** avaliar cada RF pelos critérios de qualidade (atômico, não ambíguo, verificável, completo, consistente, rastreável) e apontar lacunas que impedem a implementação — com foco nos três *Must Have* do MVP (RF01, RF04, RF02), mas cobrindo todos.

Legenda: 🔴 bloqueante · 🟠 alto · 🟡 médio · ⚪ baixo

---

## 1. Avaliação por requisito

### RF01 — Gestão de Ocorrência Policial (Must Have · UC01)

| ID | Sev. | Problema | Evidência | Recomendação |
| :--- | :---: | :--- | :--- | :--- |
| **RF-P01** | 🟠 | **Não é atômico.** Agrupa três capacidades: (a) registrar o fato, (b) qualificar envolvidos, (c) armazenar evidências. | Texto do RF01 | Desmembrar em RF01.a/b/c ou em RF01 + RF11 (evidências). Facilita o MoSCoW: evidências podem ser *Should*. |
| **RF-P02** | 🔴 | **Incompleto para o MVP.** O RF não exige **geolocalização** (latitude/longitude) nem **data/hora do fato**, mas RF02, RF05 e o mapa tático dependem disso. O diagrama de classes tem os atributos; o código não. | DIV-16 | Adicionar ao RF01: "coordenadas geográficas obrigatórias (ou obtidas por geocodificação do endereço) e data/hora do fato". |
| **RF-P03** | 🟠 | **Incompleto.** Não menciona tipificação penal (que está no escopo do MVP §3.2 e já está no código), nem geração de protocolo (que está no UC01, passo 9). | §3.2, UC01 | Trazer para o RF o que o UC já exige. |
| **RF-P04** | 🟠 | **Regra não implementada.** "No mínimo um envolvido" (UC01 regra 1) não é validada no domínio nem no formulário. | DIV-18 | Validar em `Ocorrencia` (invariante) — ver Etapa 4. |
| **RF-P05** | 🟡 | **Ambíguo.** "Registro integral" e "armazenamento permanente" não são verificáveis; "permanente" é, na verdade, um RNF (RNF03). | Texto do RF01 | Trocar por critérios: campos obrigatórios listados; evidência vinculada não pode ser desvinculada. |
| **RF-P06** | 🟡 | **Inconsistente.** Formatos de evidência aceitos divergem (`.png` × `.mp4`); tamanho máximo não é definido; sq01 menciona "validar tamanho" sem valor. | DIV-08 | Fixar: `pdf, jpg, jpeg, png`, ≤ 10 MB por arquivo (sugestão), ≤ N arquivos por ocorrência. |
| **RF-P07** | 🟡 | **Cenário ausente.** Não há RF/UC para o Agente **editar/corrigir** a ocorrência devolvida pelo Delegado (`Em Correção`), nem para reenviá-la. UC04 cita a devolução, mas o ciclo nunca fecha. | UC04 alt. I | Novo requisito (RF14 na Etapa 4). |

### RF02 — Monitoramento e Despacho Tático (Must Have · UC02)

| ID | Sev. | Problema | Evidência | Recomendação |
| :--- | :---: | :--- | :--- | :--- |
| **RF-P08** | 🔴 | **Não é atômico e esconde pré-requisitos.** Para "visualizar viaturas em tempo real" é preciso: (1) **cadastro de viaturas** (frota), (2) **ingestão de telemetria** (simulador no MVP), (3) **canal de tempo real** para o painel, (4) **cálculo de proximidade**, (5) **ordem de despacho**. Só (5) está no RF. O Planejamento (D1–D6) reconhece os cinco, mas nenhum tem RF. | Planejamento Sprint 4 | Desmembrar em RF15–RF18 (Etapa 4). Sem isso, a rastreabilidade RF → UC → código é impossível para a sprint mais pesada. |
| **RF-P09** | 🟠 | **Ambíguo.** "Unidades mais próximas" — métrica indefinida no RF; três nomes diferentes nos documentos. | DIV-07 | Fixar **Haversine** sobre a última posição válida (≤ 60 s, UC02 regra 3). |
| **RF-P10** | 🟠 | **Máquina de estados incompleta.** UC02 leva a ocorrência a `Em Atendimento` e a viatura a `Em Deslocamento`, mas **nenhum RF/UC encerra o atendimento** (`Concluída`/`Encerrada`) nem libera a viatura de volta para `Disponível`. | DIV-03 | Novo requisito de encerramento (RF19 na Etapa 4), mesmo que simplificado no MVP. |
| **RF-P11** | 🟡 | **Cenário alternativo subespecificado.** "Despacho de múltiplas viaturas" (UC02 alt. I) — `OrdemDeServico` designa `1..*` viaturas no diagrama, mas o texto de despacho é singular. Regra para a ocorrência com 2 viaturas (uma chega e a outra não) não existe. | Diagrama de classes | Manter fora do MVP; registrar como decisão. |
| **RF-P12** | 🟡 | **Verificabilidade.** "Tempo real" só ganha número no §3.4 (< 1 s). Frequência de emissão do simulador e número de viaturas simultâneas não definidos. | §3.4, D2 | Definir: simulador a 1 Hz, ≥ 3 viaturas, latência p95 < 1 s em rede local. |

### RF03 — Gestão de Inventário de Apreensões (Should · UC03)

| ID | Sev. | Problema | Recomendação |
| :--- | :---: | :--- | :--- |
| **RF-P13** | 🟡 | "Cadeia de custódia" citada, mas não modelada: não há entidade de **evento de custódia** (quem, quando, de onde, para onde). `ItemApreendido` tem apenas status. | Se RF03 entrar em ciclo futuro, criar `MovimentacaoCustodia` (append-only). |
| **RF-P14** | 🟡 | UC03 regra 3 fala em "homologação do auto", mas `AutoDeApreensao` não tem estado. Unicidade de lacre (exceção I) não está no RF. | Explicitar estados do auto e a unicidade de lacre no RF. |

### RF04 — Fluxo de Aprovação e Revisão (Must Have · UC04)

| ID | Sev. | Problema | Evidência | Recomendação |
| :--- | :---: | :--- | :--- | :--- |
| **RF-P15** | 🔴 | **Saídas da revisão inconsistentes** (2, 3 ou 2 dependendo do artefato) e semântica de `Rejeitada` × `Em Correção` indefinida (terminal? volta ao agente?). | DIV-03, DIV-05 | Definir: `Em Correção` = devolvida ao Agente, pode ser reenviada; `Rejeitada` = terminal, arquivada com justificativa. Ambas exigem justificativa. |
| **RF-P16** | 🟠 | **Depende de funcionalidade inexistente.** "Somente Delegado valida" exige autenticação + papéis (nenhum RF os descreve; RNF02 descreve o controle, não o cadastro/login). | DIV-20 | RF11/RF12 na Etapa 4. |
| **RF-P17** | 🟠 | **Depende de consulta não especificada.** UC04 começa por "fila de ocorrências pendentes" ordenada por antiguidade e gravidade; não há RF de consulta/listagem, nem atributo de gravidade. | DIV-13 | RF13 na Etapa 4; remover "gravidade" da ordenação no MVP ou adicionar atributo `prioridade` à ocorrência. |
| **RF-P18** | 🟡 | **Mecanismo indefinido.** Regra 2: "chave criptográfica de integridade que impede a edição da narrativa" — hash? assinatura? onde é guardada? O diagrama tem `chaveSeguranca: String`, mas nada define a geração. | UC04 regra 2 | No MVP: SHA-256 da narrativa + envolvidos gravado na validação; comparação em qualquer leitura (RF08 futuro reutiliza). Ou marcar como fora do MVP. |
| **RF-P19** | 🟡 | **Notificação ao Agente** (UC04 passo 9, entidade `Notificacao`) não tem RF. | UC04 | RF21 na Etapa 4 (Should). |
| **RF-P20** | 🟡 | "Assinar digitalmente o ato de validação" (passo 8) conflita com o limite do MVP (§3.2 exclui ICP-Brasil). | §3.2 | No MVP, registrar `validada_por_id` + auditoria (já há campo no código). |

### RF05 — Inteligência Criminal e Alertas (Should · UC05, UC11)

| ID | Sev. | Problema | Recomendação |
| :--- | :---: | :--- | :--- |
| **RF-P21** | 🟠 | **Dois requisitos em um** (manchas criminais × alertas automáticos), já reconhecido pela existência de UC05 e UC11 separados. | Desmembrar em RF05.a (visualização) e RF05.b (alertas). |
| **RF-P22** | 🟠 | **Gatilhos inconsistentes e não mensuráveis.** RF05: "reincidência na semana" e "aumento expressivo em 24h". UC05: "> 20% em 24h". UC11: "> 3 ocorrências na mesma semana" e "> 20%". "Expressivo" não é mensurável. | Fixar os limiares no RF (parametrizáveis). |
| **RF-P23** | 🟠 | **Dependência oculta de modelo.** Reincidência exige identificar o **mesmo suspeito** em várias ocorrências (CPF/identificador). O modelo do código (envolvido 1:N, `documento` opcional) não suporta. | Decidir na Etapa 4 (DIV-17): manter 1:N no MVP e registrar dívida. |

### RF06 — Inquéritos e Vinculação (Could · UC06)

| ID | Sev. | Problema | Recomendação |
| :--- | :---: | :--- | :--- |
| **RF-P24** | 🟡 | "Identificando automaticamente possíveis conexões" — critério algorítmico sem limiar; *modus operandi* não é atributo de nenhuma classe. | Explicitar critérios ou reduzir a "sugestão por CPF/placa comuns". |
| **RF-P25** | 🟡 | Falta RF/UC de **abertura de inquérito** (pré-condição do UC06). | DIV-15 — criar quando RF06 entrar em ciclo. |

### RF07 — Laudos Periciais (Should · UC07)

| ID | Sev. | Problema | Recomendação |
| :--- | :---: | :--- | :--- |
| **RF-P26** | 🟡 | Validação de assinatura ICP-Brasil é integração pesada e conflita com os limites do MVP; "status pericial" não tem máquina de estados definida. | Definir estados (`Requisitado → Em Análise → Laudo Concluído → Retificado`) e deixar ICP-Brasil como porta com adapter *fake* no ciclo em que entrar. |

### RF08 — Autenticação Pública de Documentos (Could · UC08)

| ID | Sev. | Problema | Recomendação |
| :--- | :---: | :--- | :--- |
| **RF-P27** | 🟠 | **Depende de RF inexistente**: emissão de documentos oficiais (BO/certidão em PDF com chave de 24 caracteres e QR Code). | DIV-14 — criar "RF de emissão de documentos" antes de RF08. |
| **RF-P28** | 🟡 | Status `Válido, Retificado, Anulado` do documento não aparece em nenhuma outra parte do modelo (anulação de BO não tem UC). | Registrar como dívida. |

### RF09 — Medidas Protetivas (Could · UC09, UC12)

| ID | Sev. | Problema | Recomendação |
| :--- | :---: | :--- | :--- |
| **RF-P29** | 🟠 | UC09 exceção I fala em "violação de perímetro" — implica rastreamento GPS de **pessoas**, inviável e não especificado. | Restringir a "descumprimento detectado por nova ocorrência com mesma vítima" (regra 3). |
| **RF-P30** | 🟡 | UC12 é um caso de uso sem identificador de RF próprio (herda RF09) e não aparece no diagrama de casos de uso. | DIV-06. |

### RF10 — Comunicação Interagências (Won't)

| ID | Sev. | Problema | Recomendação |
| :--- | :---: | :--- | :--- |
| **RF-P31** | ⚪ | "Sigilosa" sem especificação de criptografia/segregação; níveis de sigilo definidos só no UC10. | Manter em Won't; detalhar no ciclo em que entrar. |

---

## 2. Requisitos funcionais **ausentes** (transversais)

Estes comportamentos são exigidos por pré-condições, passos de UC, critérios de aceite do MVP ou tarefas do Planejamento, mas **não têm RF**:

| # | Capacidade ausente | Exigida por | Já existe no código? | Tratamento |
| :--- | :--- | :--- | :---: | :--- |
| A1 | Autenticação (login/sessão/token) | Pré-condição de todos os UCs; §3.4 critério 2; Planejamento S1 | Não (só config JWT) | **RF11** (Etapa 4) |
| A2 | Gestão de usuários e papéis (seed/admin mínimo) | RNF02; S2 | Não | **RF12** |
| A3 | Consulta de ocorrências (fila por status, ordenação, detalhe) | UC04 passos 1–4; UC02 passo 2; S3 | Parcial (`GET /{id}`, `listar` no repositório) | **RF13** |
| A4 | Correção e reenvio pelo Agente | UC04 alt. I | Não | **RF14** |
| A5 | Cadastro de viaturas | UC02; D1 | Não | **RF15** |
| A6 | Ingestão de telemetria + simulador | §3.2; UC02 pré-cond. 2; D2 | Não | **RF16** |
| A7 | Canal de tempo real (WebSocket) | §3.3 passo 3; §3.4 critério 3; D3/D4 | Não | **RF17** |
| A8 | Sugestão de viaturas próximas + ordem de despacho | UC02 passos 4–9; D5/D6 | Não | **RF18** |
| A9 | Encerramento do atendimento / liberação da viatura | §3.2 (estado `Concluída`) | Não | **RF19** |
| A10 | Registro de auditoria de operações sensíveis | RNF03; UC02 passo 9; UC04 passo 8 | Não | **RF20** |
| A11 | Notificação in-app ao Agente | UC04 passo 9 | Não | **RF21** (Should) |
| A12 | Evidências digitais (upload) | RF01; UC01 passo 5; S6 | Não | **RF22** (Should) |
| A13 | Emissão de documentos oficiais (PDF) | RF08 | Não | Fora do MVP (Etapa 5) |
| A14 | Abertura/gestão de inquérito | RF06 | Não | Fora do MVP (Etapa 5) |

---

## 3. Avaliação da Matriz MoSCoW

- A priorização **RF01 → RF04 → RF02** está correta como cadeia de valor, mas **RF02 está subdimensionado**: ele sozinho equivale a 6 fatias do Planejamento (D1–D6). Como Must Have, deveria ser desmembrado para que cada fatia tenha critério de aceite próprio.
- **RF05, RF07 (Should)** dependem de dados que o modelo atual não captura (coordenadas, identificação única de suspeito, assinatura digital). Não há risco para o MVP, mas o *Should* é otimista para o calendário de 4 sprints.
- A matriz não contempla os requisitos transversais (A1–A12), que são todos **Must** para o MVP e consomem a maior parte das Sprints 3 e 4.

---

## O que foi feito nesta etapa

1. Cada RF01–RF10 foi avaliado contra os seis critérios de qualidade; **31 problemas** registrados (`RF-P01`…`RF-P31`), com severidade e recomendação.
2. Cruzamento de cada RF com seus UCs (texto + diagrama de sequência) e com o Planejamento, para localizar **14 capacidades sem requisito** (A1–A14).
3. Avaliação crítica da matriz MoSCoW frente ao calendário.
4. Nenhum documento original alterado.

**Próxima etapa:** análise dos RNF01–RNF05 e RNFs ausentes (`ETAPA-03`).
