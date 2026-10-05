# 🛡️ Roteiro Consolidado de Demonstração, Seeds e Ensaio para a Banca Final

> **Projeto:** Sistema de Gestão de Ocorrências Policiais Integradas (SGOPI Sentinela)  
> **Instituição:** Universidade Federal do Pampa (Unipampa — Campus Alegrete)  
> **Disciplina:** Resolução de Problemas IV (AL0343)  
> **Docentes Avaliadores:** Prof. Dr. Gilleanes Thorwald Araujo Guedes / Prof. Dr. Fabio Paulo Basso  
> **Tempo Total Alocado:** 10 minutos cronometrados (+ 5 minutos de arguição técnica)

---

## 🧭 Visão Geral e Estrutura da Apresentação

O objetivo desta demonstração ao vivo é comprovar o funcionamento pleno do MVP do **SGOPI Sentinela** operando sob a **Arquitetura Dual (Portal Público do Cidadão + Painel Operacional Policial)** e demonstrar o cumprimento estrito dos requisitos canônicos:

* **RF01:** Gestão e Registro Circunstanciado de Ocorrências Policiais (com qualificação de envolvidos, tipificações e evidências digitais imutáveis);
* **RF04:** Fluxo de Homologação, Triagem e Revisão Jurídica pelo Delegado (com congelamento de integridade via hash SHA-256);
* **RF02:** Monitoramento Tático em Tempo Real (WebSockets), Telemetria GPS de Viaturas em Alegrete-RS e Despacho Tático por Cálculo de Proximidade (Haversine/Euclidiano);
* **RNF01 a RNF05:** Desempenho e baixa latência, RBAC estrito, tabelas append-only sem deleções físicas, tolerância a falhas e desacoplamento na Arquitetura Hexagonal (*Ports & Adapters*).

---

## ⏱️ Cronograma Cronometrado (10 Minutos)

| Minuto | Bloco / Persona | Foco da Apresentação | Apresentador Sugerido |
| :---: | :--- | :--- | :--- |
| **00:00 - 01:30** | **1. Abertura & Arquitetura** | Contextualização do problema de segurança pública, divisão hexagonal estrita (`domain/` puro) e critérios de qualidade (zero violações no `import-linter`, cobertura acima da meta de 80%). | **Rodrigo Thoma** |
| **01:30 - 04:00** | **2. Cidadão (Portal Sentinela)** | Landing Page com aletas mecânicas (`SplitFlapText`), registro de furto no mapa Leaflet, emissão do protocolo oficial e consulta pública do status, sem exposição de dados pessoais (LGPD). | **Fade Kanaan** |
| **04:00 - 06:15** | **3. Delegada (Triagem Policial)** | Login rápido (`delegado`), fila de triagem, inspeção da ocorrência de furto, validação formal de evidências e congelamento da narrativa com hash criptográfico SHA-256. | **Mateus Valau** |
| **06:15 - 08:30** | **4. Operador (Comando Tático)** | Centro de Comando GPS em tempo real, telemetria WebSocket (< 1s), seleção da ocorrência validada, sugestão das 3 viaturas mais próximas via Haversine e ordem de despacho. | **Matheus Cabral** |
| **08:30 - 09:30** | **5. Auditoria & Resiliência** | Trilha append-only (`registros_auditoria`), mecanismo de tolerância a falhas GPS (fallback tabular) e integridade de dados. | **Gabriel Ortiz** |
| **09:30 - 10:00** | **6. Conclusão & Qualidade** | Síntese de engenharia de software, aderência aos padrões SOLID e abertura para a banca avaliadora. | **Gustavo dos Anjos** |

---

## 🚀 Setup Rápido do Ambiente Pré-Banca (1 Comando)

Antes de iniciar a apresentação, certifique-se de que a base de dados foi semeada com dados atualizados e georreferenciados:

```bash
# 1. Certifique-se de que o Postgres local está ativo
docker compose up -d

# 2. Na pasta backend: aplique migrações e rode o seed oficial
cd backend
uv run alembic upgrade head
uv run python -m scripts.seed

# 3. Suba a API
uv run uvicorn --app-dir src main:app --reload

# 4. Em outro terminal, na pasta frontend: suba a interface web
cd ../frontend
npm run dev
```

* **Frontend:** `http://localhost:3000`
* **API Swagger:** `http://localhost:8000/docs`

### 🌱 Modo vivo — gerador de ocorrências fictícias (Issue #55, opt-in · extra, fora do MVP)

Alimenta a **Fila do Delegado** com 1 ocorrência `AGUARDANDO_REVISAO` marcada com
`[SIMULADO-DEMO]` (autor `simulador-demo`) a cada intervalo. Aparece na fila após
refresh; **painel tático/heatmap só refletem após validação manual** (o painel lista
só `VALIDADA`/`EM_ATENDIMENTO`).

```bash
cd backend
# .env: GERADOR_OCORRENCIAS_LIGADO=true  (intervalo padrão 120s, mínimo 1s)
uv run uvicorn --app-dir src main:app --reload
```

* Sem `simulador-demo` no banco: o gerador loga `rode o seed` e não inicia, sem derrubar o servidor — rode `uv run python -m scripts.seed`.
* Limpeza: reset do banco demo (`docker compose down -v && docker compose up -d && uv run alembic upgrade head && uv run python -m scripts.seed`).
* Fora de escopo: atualização da fila via WebSocket em tempo real e mudança no filtro do heatmap.

### ⚙️ Despacho e encerramento automáticos (Issues #62/#63, opt-in · extra, fora do MVP)

Um **orquestrador de despacho** observa o banco a cada `ORQUESTRADOR_INTERVALO_SEGUNDOS`
(padrão 5s). Para cada ocorrência `VALIDADA` esperando além de `JANELA_CARENCIA_SEGUNDOS`
(20s), ele escolhe a viatura `DISPONIVEL` mais próxima pelo **mesmo** serviço de sugestão
do painel (Haversine + `posicao_valida`/RNF04) e despacha chamando os **mesmos casos de
uso** do Operador (`DespacharViatura`/`EncerrarOcorrencia`). A viatura avança até o local
(telemetria), e após `TEMPO_ATENDIMENTO_SEGUNDOS` (45s) desde a chegada o encerramento é
feito pelo Delegado simulado — auditável e append-only como o fluxo manual.

```bash
cd backend
# .env:
#   DESPACHO_AUTOMATICO_LIGADO=true
#   ORQUESTRADOR_INTERVALO_SEGUNDOS=5   (mínimo 1s)
#   JANELA_CARENCIA_SEGUNDOS=20
#   TEMPO_ATENDIMENTO_SEGUNDOS=45
uv run uvicorn --app-dir src main:app --reload
```

* Liga junto com a telemetria (`POST /v1/simulador/ligar`); o indicador **"Despacho automático ativo"** aparece no Painel Tático ao lado do botão do simulador, com os contadores de despachadas/encerradas.
* Atores: `simulador-operador` (despacho) e `simulador-delegado` (encerramento) — criados pelo seed com senha inutilizável; se ausentes, loga `rode o seed`.
* **Demonstração:** 1) subir com as flags acima; 2) a `SGOPI-YYYY-000012` (Disparos, Bairro Piola) já é semeada como `VALIDADA`, aguardando despacho (opcionalmente, valide outra ocorrência como Delegada); 3) ligar o simulador no Painel Tático — o orquestrador despacha sozinho, a VTR avança no mapa, a ocorrência encerra em ~45s e sai da lista.
* Reset do cenário: recriar o banco demo. O seed é **idempotente**: a VTR-02 só reposiciona (B2) em banco recriado.

---

## 🎭 Roteiro Passo a Passo de Demonstração Ao Vivo

### Bloco 1: Abertura e Arquitetura Hexagonal (00:00 - 01:30)
* **Objetivo:** Estabelecer a seriedade da engenharia de software antes de exibir telas.
* **Ação na Tela:** Deixar aberto o slide ou o diagrama de pacotes [`docs/diagramas/diagrama-pacotes-arquitetura-hexagonal.png`](diagramas/diagrama-pacotes-arquitetura-hexagonal.png) ou o terminal com o resultado do *import-linter*.
* **Falas-Chave:**
  > *"Boa tarde, professores Gilleanes e Fabio. O SGOPI Sentinela foi desenvolvido sob os princípios da Arquitetura Hexagonal com isolamento absoluto do domínio: nossa camada de domínio não importa nenhuma dependência externa, nem FastAPI nem SQLAlchemy. O sistema adota uma Arquitetura Dual: acolhe o registro público do cidadão sem burocracia e entrega à autoridade policial ferramentas de triagem e inteligência operacional em tempo real."*
* **Destaques Técnicos:**
  * Apresentar o resultado dos testes (pytest com cobertura, Cypress e E2E de API) — use os números atualizados da tabela *Qualidade* do [README](../README.md#qualidade);
  * Regra de ouro da arquitetura verificada pelo `import-linter`.

---

### Bloco 2: Persona Cidadão — Delegacia Eletrônica (01:30 - 04:00)
* **Objetivo:** Demonstrar o canal público sem autenticação e a experiência do cidadão (**RF01** + **RNF02**).
* **Ação na Tela:**
  1. Acessar `http://localhost:3000/` (Landing Page com display de aletas e identidade visual do Sentinela);
  2. Clicar em **"Registrar Ocorrência"** (`/registrar-cidadao`);
  3. Preencher o formulário simplificado:
     * **Nome:** Cidadão Demonstrador;
     * **CPF:** `123.456.789-09` (mostrar validação algorítmica de CPF);
     * **Contato:** `cidadao@exemplo.com` / `(55) 99988-7766`;
     * **Tipo:** Furto;
     * **Relato circunstanciado:** *"Extravio de mochila contendo documentos e chaves no banco da praça central."* (mostrar contagem regressiva de caracteres, mínimo de 20);
     * **Localização com Mapa Interativo:** Clicar no mapa Leaflet para posicionar o pin na região de Alegrete-RS (coordenadas preenchidas automaticamente);
  4. Marcar a declaração legal e clicar em **"Confirmar e Transmitir Comunicação"**;
  5. **Comprovante Gerado:** Copiar o número de protocolo oficial (em banco recém-semeado, o primeiro registro ao vivo recebe `SGOPI-2026-000013`, pois o seed ocupa de `000001` a `000012`);
  6. Clicar em **"Consultar Tramitação"** (ou acessar `/consulta`), colar o protocolo e exibir as etapas de status (Triagem Policial → Validada → Em Atendimento → Finalizada), com a ocorrência em triagem (`Aguardando Revisão`). A consulta pública mostra apenas dados gerais do fato (protocolo, status, natureza, localização e data) e **não expõe dados pessoais** dos envolvidos (**RNF02** / LGPD).
* **Falas-Chave:**
  > *"O cidadão consegue registrar a ocorrência em menos de 2 minutos diretamente pelo navegador do celular ou computador. O sistema gera um protocolo único e protege dados pessoais: a consulta pública não exibe nenhum dado dos envolvidos, apenas o andamento do registro."*

---

### Bloco 3: Persona Delegada — Triagem e Validação Jurídica (04:00 - 06:15)
* **Objetivo:** Demonstrar o controle de acesso por papéis (**RNF02**) e o fluxo formal de homologação (**RF04** / **RNF03**).
* **Ação na Tela:**
  1. Acessar `http://localhost:3000/login`;
  2. Utilizar o botão de atalho de demonstração **"Delegado"** (`delegado` / `Senha@123`);
  3. Acessar a **Fila de Triagem** (`/fila` ou pelo menu de navegação);
  4. Observar a ocorrência recém-criada pelo cidadão e a ocorrência semeada `SGOPI-2026-000001` (Furto na Praça Getúlio Vargas);
  5. Abrir os detalhes da ocorrência `SGOPI-2026-000001`:
     * Mostrar a qualificação formal dos envolvidos (Vítima e Comunicante);
     * Mostrar a tipificação legal vinculada (`Art. 155, CP`);
     * Mostrar o histórico de status;
  6. No campo **Despacho da autoridade**, informar *"Regularidade formal verificada pela autoridade policial."* e clicar em **"Validar"**;
  7. **Resultado Imediato:** O status muda para `Validada`, o despacho aparece no detalhe e no histórico, a operação é auditada e a ocorrência recebe seu `hash_narrativa` imutável em SHA-256;
  8. Recarregar o detalhe para comprovar a persistência do despacho e alternar para o **Agente autor**, em **Minhas ocorrências**, para demonstrar sua consulta posterior.
* **Falas-Chave:**
  > *"Somente usuários com perfil de Delegado possuem autorização no backend para validar ocorrências. O despacho é opcional, mas, quando informado, integra a decisão formal e é preservado no agregado, no histórico append-only e na auditoria, sem alterar o hash da narrativa ou a máquina de estados."*

---

### Bloco 4: Persona Operador — Centro de Comando Tático & Despacho (06:15 - 08:30)
* **Objetivo:** Demonstrar mapa tático em tempo real, telemetria GPS e cálculo de proximidade (**RF02** / **RNF01**).
* **Ação na Tela:**
  1. Alternar sessão para **Operador da Central** (`operador` / `Senha@123`);
  2. Acessar o **Painel Tático** (`/painel` ou pelo menu de navegação);
  3. **Visualização do Mapa:**
     * Exibir as viaturas de Alegrete (`VTR-01` a `VTR-05`) plotadas dinamicamente com seus badges de situação (`Disponível`, `Em Deslocamento`);
     * Destacar que a telemetria é consumida via conexão bidirecional WebSockets;
  4. **Execução do Despacho Tático:**
     * Selecionar a ocorrência `SGOPI-2026-000002` (Roubo na Av. Tiaraju);
     * Apontar que o sistema calcula e ordena as viaturas mais próximas usando o algoritmo geodésico de Haversine;
     * Confirmar o despacho da `VTR-01` (mais próxima);
     * Observar a atualização reativa da viatura para `Em Deslocamento` e a emissão formal da Ordem de Despacho com operador, viatura e data/hora.
* **Falas-Chave:**
  > *"O operador da central tem consciência situacional completa. O sistema elimina a adivinhação ao calcular instantaneamente as viaturas mais próximas por proximidade euclidiana/Haversine, emitindo ordens de serviço auditáveis."*

---

### Bloco 5: Auditoria, Imutabilidade e Tolerância a Falhas (08:30 - 09:30)
* **Objetivo:** Comprovar a solidez arquitetural e o cumprimento dos requisitos não-funcionais (**RNF03** e **RNF04**).
* **Ação na Tela:**
  1. Mostrar o histórico de status de uma ocorrência encerrada (`SGOPI-2026-000004`), comprovando a rastreabilidade ponta a ponta: `Aguardando Revisão` $\rightarrow$ `Validada` $\rightarrow$ `Em Atendimento` $\rightarrow$ `Encerrada`;
  2. Apresentar o conceito de tabela **append-only** (auditoria e histórico de status) e a ausência de deleções físicas: ocorrências só saem do fluxo por status (`ARQUIVADA`/`EXCLUIDA`, com motivo) e viaturas por situação `INDISPONIVEL`;
  3. **Resiliência (RNF04):** Explicar a estratégia de degradação graciosa: se o simulador de telemetria ou o WebSocket cair, o painel tático preserva a última posição conhecida em listagem tabular, garantindo que o despacho manual continue operando.
* **Falas-Chave:**
  > *"Em conformidade com o RNF03, registros de auditoria e histórico de status são estritamente incrementais (append-only). Nem mesmo administradores podem alterar logs passados."*

---

### Bloco 6: Conclusão e Arguição (09:30 - 10:00)
* **Ação na Tela:** Retornar à página inicial ou aos slides finais com o resumo das métricas de engenharia.
* **Falas-Chave:**
  > *"Concluímos a apresentação do MVP do SGOPI Sentinela demonstrando 100% de aderência aos requisitos RF01, RF04 e RF02, fundamentados em Arquitetura Hexagonal, SOLID e auditoria rigorosa. Agradecemos aos professores e estamos prontos para a arguição."*

---

## 📋 Tabela de Dados Semeados (Referência Rápida para a Demo)

O seed cria **12 ocorrências** (`SGOPI-2026-000001` a `000012`) e **5 viaturas**. Usuários com login: `agente`, `delegado` e `operador` (senha `Senha@123`); os atores `simulador-demo`, `simulador-operador` e `simulador-delegado` têm senha inutilizável e servem apenas aos extras opcionais.

| Protocolo / Prefixo | Tipo / Papel | Local / Endereço | Status Inicial | Ação Prevista na Demo |
| :--- | :--- | :--- | :--- | :--- |
| `SGOPI-2026-000001` | Furto (Bicicleta) | Praça Getúlio Vargas | `AGUARDANDO_REVISAO` | Homologar ao vivo como Delegada |
| `SGOPI-2026-000002` | Roubo Comercial | Av. Tiaraju, 1250 | `VALIDADA` | Despachar ao vivo como Operador |
| `SGOPI-2026-000003` | Acidente de Trânsito | Rua dos Andradas | `EM_ATENDIMENTO` | Demonstrar viatura VTR-02 em trânsito |
| `SGOPI-2026-000004` | Perturbação de Sossego | Rua Barão do Cerro Largo | `ENCERRADA` | Exibir histórico e desfecho concluído |
| `SGOPI-2026-000005` | Dano ao Patrimônio | Av. Assis Brasil | `EM_CORRECAO` | Exibir justificativa de devolução |
| `SGOPI-2026-000006` | Tráfico de Entorpecentes | Rua Venâncio Aires, 450 | `VALIDADA` | Reserva para despacho / mapa |
| `SGOPI-2026-000007` | Roubo a Transeunte | Parque Rui Ramos | `VALIDADA` | Reserva para despacho / mapa |
| `SGOPI-2026-000008` | Receptação de Veículo | Rua Bento Manoel, Estação Férrea | `VALIDADA` | Reserva para despacho / mapa |
| `SGOPI-2026-000009` | Dano Qualificado | Praça Oswaldo Aranha | `VALIDADA` | Reserva para despacho / mapa |
| `SGOPI-2026-000010` | Violência Doméstica / Ameaça | Rua Marquês de Olinda, Ibirapuitã | `VALIDADA` | Reserva para despacho / mapa |
| `SGOPI-2026-000011` | Furto Qualificado | Av. Freitas Valle, Santos Dumont | `VALIDADA` | Reserva para despacho / mapa |
| `SGOPI-2026-000012` | Disparo de Arma de Fogo | Rua Dr. Lauro Dornelles, Piola | `VALIDADA` | Despacho automático (extra opcional) |
| `VTR-01` | Viatura Ostensiva | Centro (-29.7842, -55.7932) | `DISPONIVEL` | Despachar para ocorrência 000002 |
| `VTR-02` | Viatura Tática | Centro (–29.7863, –55.7930) — desloca até Rua dos Andradas | `EM_DESLOCAMENTO` | Em atendimento da ocorrência 000003 |
| `VTR-03` | Viatura Ronda | Rui Ramos (-29.7785, -55.7915) | `DISPONIVEL` | Unidade de apoio |
| `VTR-04` | Viatura Ronda | Assis Brasil (-29.7910, -55.7890) | `DISPONIVEL` | Unidade de apoio |
| `VTR-05` | Viatura Patrulha | Cidade Alta (-29.7750, -55.8010) | `DISPONIVEL` | Unidade de apoio |

---

## 🛡️ Plano de Contingência Técnica (O que fazer se...)

1. **A porta 8000 ou 3000 estiver ocupada:**
   * Rodar `lsof -i :8000` / `lsof -i :3000` e finalizar os processos anteriores com `kill -9`.
2. **O banco PostgreSQL local estiver com dados corrompidos de testes anteriores:**
   * Executar: `docker compose down -v && docker compose up -d && cd backend && uv run alembic upgrade head && uv run python -m scripts.seed`.
3. **O navegador perder conexão WebSocket durante a apresentação:**
   * A aplicação exibe alerta de desconexão e mantém os últimos dados conhecidos em tela sem travar a interface. Um simples `F5` reconecta automaticamente.
