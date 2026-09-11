# 🗓️ Planejamento de Desenvolvimento — SGOPI Sentinela

Plano de trabalho semanal até a apresentação final do **SGOPI Sentinela**. Complementa a [Documentação de Engenharia](DOCUMENTACAO_DE_ENGENHARIA.md), que define *o que* será construído.

---

## 🧭 Sumário

1. [Calendário](#-calendário)
2. [Princípios do plano](#princípios-do-plano)
3. [Sprint 2 — Fundação](#sprint-2--fundação-111309)
4. [Sprint 3 — Registro e validação](#sprint-3--registro-e-validação-152009)
5. [Sprint 4 — Despacho tático](#sprint-4--despacho-tático-222709)
6. [Sprint 5 — Qualidade e entrega](#sprint-5--qualidade-e-entrega-29090410)

---

## 📅 Calendário

| Período | Descrição | Entrega |
| :--- | :--- | :--- |
| 11–13/09 | **Sprint 2** — fundação | — |
| **14/09** (seg) | Verificação 1 | Código próprio de cada integrante |
| 15–20/09 | **Sprint 3** — registro e validação | — |
| **21/09** (seg) | Verificação 2 | Registrar e validar ocorrência ao vivo |
| 22–27/09 | **Sprint 4** — despacho tático | — |
| **28/09** (seg) | Verificação 3 *(última antes da final)* | MVP ponta a ponta · **escopo congelado** |
| 29/09–04/10 | **Sprint 5** — qualidade e entrega | — |
| **05/10** (seg) | **Apresentação final** | Sistema completo, documentado e ensaiado |

---

## Princípios do plano

| # | Princípio | Por quê |
| :---: | :--- | :--- |
| **01** | **Uma fatia vertical por pessoa** | Cada integrante entrega funcionalidade inteira, tela, API, caso de uso, domínio e banco. É o que permite mostrar trabalho próprio na segunda sem depender de ninguém. |
| **02** | **Rotação de peso** | Quem pegou uma fatia com peso de interface leva uma de domínio ou infraestrutura no sprint seguinte. É o mecanismo que impede ilhas de conhecimento ao longo das quatro semanas. |
| **03** | **Contratos antes do código** | Portas, DTOs e schemas da API devem ser acordados **antes** de qualquer um começar. Sem isso, pode haver colisão nos mesmos arquivos. |
| **04** | **Essencial ou trocável** | Toda tarefa carrega uma das duas marcas. Trocável pode ser substituída sem renegociar o sprint. |

---

## Sprint 2 — Fundação (11–13/09)

> **Meta:** o registro de ocorrência atravessa o sistema inteiro, formulário, API, caso de uso, domínio e Postgres, mesmo que de forma mínima, **com commit próprio de cada integrante**.

**Estado atual do código:** só existe a entidade `domain/ocorrencia.py`. Todo o resto do esqueleto (portas, caso de uso, testes) está com docstring vazia.


### Tarefas

| Cód. | Tarefa | Toca | Prova na segunda | Marca |
| :---: | :--- | :--- | :--- | :---: |
| **T1** | **Ambiente reproduzível** — Docker Compose com Postgres, `.env.example`, README de setup, `uv sync` funcionando e endpoint `/health` verificando a conexão com o banco | `infra` `backend` `docs` | Um colega clona o repositório, sobe tudo com um comando e vê `/health` respondendo | `Essencial` |
| **T2** | **Domínio completo da ocorrência** — envolvidos (vítima, testemunha, suspeito), tipificação penal e evidências | `domínio` `testes` | `uv run pytest` verde cobrindo as regras do UC01 | `Essencial` |
| **T3** | **Portas e caso de uso** — DTOs de entrada e saída, contrato das portas, `RegistrarOcorrenciaPolicial` implementado | `aplicação` `testes` | Caso de uso testado com repositório fake, sem banco nem servidor | `Essencial` |
| **T4** | **Persistência em Postgres** — modelos SQLAlchemy, migração com Alembic, DAO implementando a porta | `adapters` `banco` | Tabelas criadas por migração e uma ocorrência salva de verdade | `Essencial` |
| **T5** | **API de registro** — rota `POST /ocorrencias`, schemas Pydantic, injeção via `Depends` | `adapters` `backend` | Swagger em `/docs` aceitando um registro completo | `Essencial` |
| **T6** | **Formulário de registro** — esqueleto do frontend e a tela do agente enviando para a API | `frontend` | Formulário que envia e devolve o número de protocolo gerado | `Essencial` |

---

## Sprint 3 — Registro e validação (15–20/09)

> **Meta:** o agente registra, o delegado valida, o status muda. Primeira demo com dois papéis reais interagindo.

| Cód. | Fatia | Toca | Defesa na segunda | Marca |
| :---: | :--- | :--- | :--- | :---: |
| **S1** | **Login e sessão** — tela de entrada, endpoint de autenticação, tabela de usuários | `frontend` `backend` `banco` | Entrar com usuário e senha e receber um token válido | `Essencial` |
| **S2** | **Papéis e permissões** — papel no token, guarda nas rotas, UI que esconde o que o papel não pode fazer (RNF02) | `frontend` `backend` `domínio` | Agente é recusado ao tentar validar; Delegado passa | `Essencial` |
| **S3** | **Fila de triagem** — tela de lista do Delegado, consulta filtrada por status, ordenada por antiguidade (UC04) | `frontend` `backend` `banco` | Lista mostrando só o que aguarda revisão, mais antigo primeiro | `Essencial` |
| **S4** | **Validar e rejeitar** — ação na tela, endpoint de decisão, transições no domínio, justificativa obrigatória na rejeição | `frontend` `backend` `domínio` | Status muda pela tela; rejeição sem justificativa é barrada | `Essencial` |
| **S5** | **Envolvidos múltiplos** — interface para qualificar vítimas, testemunhas e suspeitos, com tabela e relacionamento | `frontend` `backend` `banco` | Registro com três envolvidos de tipos diferentes, recuperado no detalhe | `Essencial` |
| **S6** | **Evidências digitais** — upload no formulário, endpoint de recebimento, validação de formato, vínculo permanente | `frontend` `backend` `banco` | Anexo enviado e listado; formato inválido recusado | `Essencial` |

**Dependência de calendário:** a fatia **S1 (login)** é base para as outras cinco e precisa sair até terça.

---

## Sprint 4 — Despacho tático (22–27/09)

> **Meta:** o MVP inteiro demonstrável. Semana mais pesada e última verificação antes da apresentação, o que não estiver bom aqui dificilmente entra depois.

| Cód. | Fatia | Toca | Defesa na segunda | Marca |
| :---: | :--- | :--- | :--- | :---: |
| **D1** | **Cadastro de viaturas** — entidade `Viatura`, tela de gestão da frota, status de disponibilidade | `domínio` `frontend` `banco` | Frota cadastrada, com viaturas disponíveis e indisponíveis | `Essencial` |
| **D2** | **Simulador de telemetria** — serviço emitindo coordenadas periódicas, endpoint de ingestão, persistência da última posição e painel para ligar e desligar o simulador | `backend` `frontend` `banco` | Três viaturas atualizando posição sozinhas, controladas pelo painel | `Essencial` |
| **D3** | **Canal de tempo real** — endpoint WebSocket e cliente que conecta, reconecta sozinho e recebe atualizações | `backend` `frontend` `websocket` | Navegador recebendo posições sem recarregar a página | `Essencial` |
| **D4** | **Mapa tático** — endpoint de carga inicial das posições, Leaflet sobre OpenStreetMap, marcadores de viaturas e ocorrências pendentes atualizando ao vivo | `frontend` `backend` `websocket` | Viaturas se movendo no mapa com latência abaixo de 1 s (RNF01) | `Essencial` |
| **D5** | **Cálculo de proximidade** — Haversine no domínio, endpoint que ordena viaturas disponíveis, lista de sugestões na UI | `domínio` `backend` `frontend` | Selecionar uma ocorrência e ver as três mais próximas, na ordem certa | `Essencial` |
| **D6** | **Ordem de despacho** — confirmação, transições de status da viatura e da ocorrência, registro com data, operador e protocolo | `frontend` `backend` `domínio` | Viatura `Em Deslocamento` e ocorrência `Em Atendimento` após confirmar | `Essencial` |

---

## Sprint 5 — Qualidade e entrega (29/09–04/10)

> **Meta:** nenhuma funcionalidade nova. A semana existe para transformar código que funciona em entrega defensável.

| Cód. | Frente | Toca | Entrega | Marca |
| :---: | :--- | :--- | :--- | :---: |
| **F1** | **E2E do registro** — fluxo do UC01 automatizado com Selenium | `qa` `frontend` | Script que preenche o formulário e confere o protocolo | `Essencial` |
| **F2** | **E2E de validação e despacho** — fluxo do UC04 e UC02 automatizados | `qa` `frontend` | Script que valida uma ocorrência e despacha uma viatura | `Essencial` |
| **F3** | **Cobertura acima de 80% no core** — medida sobre domínio e casos de uso | `qa` `domínio` | Relatório de cobertura anexado ao repositório | `Essencial` |
| **F4** | **Seed de dados e roteiro de demo** — script que carrega ocorrências, viaturas e usuários | `banco` `backend` | Um comando deixa o sistema pronto para demonstrar | `Essencial` |
| **F5** | **Documentação alinhada ao código** — atualizar doc de engenharia e Wiki, e corrigir no código as divergências de nomenclatura encontradas | `docs` `domínio` | Documento sem divergências com o que roda | `Essencial` |
| **F6** | **Integração final em `main`** — merge de `dev`, revisão dos PRs pendentes e correção dos bugs encontrados na integração | `git` `backend` `frontend` | `main` roda do zero numa máquina limpa | `Essencial` |

---

<div align="center">

*Revisar toda semana após a verificação*

</div>
