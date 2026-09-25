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
| **00:00 - 01:30** | **1. Abertura & Arquitetura** | Contextualização do problema de segurança pública, divisão hexagonal estrita (`domain/` puro) e critérios de qualidade (zero violações no `import-linter`, > 97% de cobertura). | **Rodrigo Thoma** |
| **01:30 - 04:00** | **2. Cidadão (Portal Sentinela)** | Landing Page com aletas mecânicas (`SplitFlapText`), registro de furto no mapa Leaflet, emissão do protocolo oficial e consulta imediata com máscara de CPF (LGPD). | **Fade Kanaan** |
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

### 🌱 Modo vivo — gerador de ocorrências fictícias (Issue #55, opt-in)

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

---

## 🎭 Roteiro Passo a Passo de Demonstração Ao Vivo

### Bloco 1: Abertura e Arquitetura Hexagonal (00:00 - 01:30)
* **Objetivo:** Estabelecer a seriedade da engenharia de software antes de exibir telas.
* **Ação na Tela:** Deixar aberto o slide ou o diagrama de pacotes [`docs/diagramas/diagrama-pacotes-arquitetura-hexagonal.png`](file:///home/thoma/workspace/sgopi-sentinela/docs/diagramas/diagrama-pacotes-arquitetura-hexagonal.png) ou o terminal com o resultado do *import-linter*.
* **Falas-Chave:**
  > *"Boa tarde, professores Gilleanes e Fabio. O SGOPI Sentinela foi desenvolvido sob os princípios da Arquitetura Hexagonal com isolamento absoluto do domínio: nossa camada de domínio não importa nenhuma dependência externa, nem FastAPI nem SQLAlchemy. O sistema adota uma Arquitetura Dual: acolhe o registro público do cidadão sem burocracia e entrega à autoridade policial ferramentas de triagem e inteligência operacional em tempo real."*
* **Destaques Técnicos:**
  * Apresentar o resultado dos testes: 295 testes automatizados com cobertura superior a 97%;
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
  4. Clicar em **Enviar Ocorrência**;
  5. **Comprovante Gerado:** Copiar o número de protocolo oficial (ex: `SGOPI-2026-000006`);
  6. Navegar para **"Consultar Ocorrência"** (`/consultar`), colar o protocolo e exibir a linha do tempo com status `Aguardando Revisão` e os dados sensíveis estritamente mascarados (**RNF02** / LGPD).
* **Falas-Chave:**
  > *"O cidadão consegue registrar a ocorrência em menos de 2 minutos diretamente pelo navegador do celular ou computador. O sistema gera um protocolo único nacional e protege dados pessoais, ocultando CPFs de terceiros na consulta pública."*

---

### Bloco 3: Persona Delegada — Triagem e Validação Jurídica (04:00 - 06:15)
* **Objetivo:** Demonstrar o controle de acesso por papéis (**RNF02**) e o fluxo formal de homologação (**RF04** / **RNF03**).
* **Ação na Tela:**
  1. Acessar `http://localhost:3000/login`;
  2. Utilizar o botão de atalho de demonstração **"Delegado"** (`delegado` / `Senha@123`);
  3. Acessar a **Fila de Triagem** (`/fila-delegado`);
  4. Observar a ocorrência recém-criada pelo cidadão e a ocorrência semeada `SGOPI-2026-000001` (Furto na Praça Getúlio Vargas);
  5. Abrir os detalhes da ocorrência `SGOPI-2026-000001`:
     * Mostrar a qualificação formal dos envolvidos (Vítima e Comunicante);
     * Mostrar a tipificação legal vinculada (`Art. 155, CP`);
     * Mostrar integridade da cadeia de custódia e histórico de status;
  6. Clicar em **"Validar Ocorrência"**;
  7. **Resultado Imediato:** O status muda para `Validada`, é disparado evento de domínio e a ocorrência recebe seu `hash_narrativa` imutável em SHA-256.
* **Falas-Chave:**
  > *"Somente usuários com perfil de Delegado possuem autorização no backend para validar ocorrências. No momento da validação, o sistema calcula o hash criptográfico da narrativa: qualquer adulteração posterior na base de dados quebraria a integridade da prova."*

---

### Bloco 4: Persona Operador — Centro de Comando Tático & Despacho (06:15 - 08:30)
* **Objetivo:** Demonstrar mapa tático em tempo real, telemetria GPS e cálculo de proximidade (**RF02** / **RNF01**).
* **Ação na Tela:**
  1. Alternar sessão para **Operador da Central** (`operador` / `Senha@123`);
  2. Acessar o **Painel Tático** (`/painel-tatico`);
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
  2. Apresentar o conceito de tabela **append-only**: nenhuma ocorrência, viatura ou log é deletado fisicamente do banco de dados;
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

| Protocolo / Prefixo | Tipo / Papel | Local / Endereço | Status Inicial | Ação Prevista na Demo |
| :--- | :--- | :--- | :--- | :--- |
| `SGOPI-2026-000001` | Furto (Bicicleta) | Praça Getúlio Vargas | `AGUARDANDO_REVISAO` | Homologar ao vivo como Delegada |
| `SGOPI-2026-000002` | Roubo Comercial | Av. Tiaraju, 1250 | `VALIDADA` | Despachar ao vivo como Operador |
| `SGOPI-2026-000003` | Acidente de Trânsito | Rua dos Andradas | `EM_ATENDIMENTO` | Demonstrar viatura VTR-02 em trânsito |
| `SGOPI-2026-000004` | Perturbação de Sossego | Rua Barão do Cerro Largo | `ENCERRADA` | Exibir histórico e desfecho concluído |
| `SGOPI-2026-000005` | Dano ao Patrimônio | Av. Assis Brasil | `EM_CORRECAO` | Exibir justificativa de devolução |
| `VTR-01` | Viatura Ostensiva | Centro (-29.7842, -55.7932) | `DISPONIVEL` | Despachar para ocorrência 000002 |
| `VTR-02` | Viatura Tática | Andradas (-29.7880, -55.7910) | `EM_DESLOCAMENTO` | Em atendimento da ocorrência 000003 |
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
