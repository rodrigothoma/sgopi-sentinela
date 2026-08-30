# 🛡️ SGOPI Sentinela — Sistema de Gestão de Ocorrências Policiais Integradas

[![Arquitetura Hexagonal](https://img.shields.io/badge/Architecture-Hexagonal%20Ports%20%26%20Adapters-blue.svg)](#-arquitetura-do-software)
[![UML](https://img.shields.io/badge/Modelagem-UML-green.svg)](docs/DOCUMENTACAO_DE_ENGENHARIA.md)
[![Unipampa](https://img.shields.io/badge/Unipampa-Engenharia%20de%20Software-red.svg)](https://unipampa.edu.br/alegrete/)

O **SGOPI Sentinela** é uma solução de software para segurança pública desenvolvida com foco em **alta confiabilidade, tempo real, integridade de auditoria e desacoplamento arquitetural**. O sistema abrange desde o registro circunstanciado de ocorrências policiais e triagem técnica pelo Delegado até o monitoramento georreferenciado de viaturas em tempo real, inteligência de manchas criminais e gestão da cadeia de custódia.

O projeto e a arquitetura foram concebidos e modelados inicialmente na disciplina de **Análise e Projeto de Software (AL0332)**. Na disciplina atual de **Resolução de Problemas IV (AL0343)** do curso de **Engenharia de Software da Universidade Federal do Pampa (Unipampa - Campus Alegrete)**, a equipe consolidou a documentação técnica, a modelagem UML e o planejamento do MVP para guiar o ciclo de desenvolvimento e implementação do software.

---

## 📚 Documentação Técnica e Wiki

| Documento | Localização | Descrição |
| :--- | :--- | :--- |
| 📄 **Especificação Completa de Engenharia** | [**docs/DOCUMENTACAO_DE_ENGENHARIA.md**](docs/DOCUMENTACAO_DE_ENGENHARIA.md) | Documento principal com a especificação de requisitos (RF01 a RF10, RNF01 a RNF05), matriz MoSCoW, proposta de MVP, padrões de projeto e os 11 casos de uso acompanhados de seus diagramas de sequência. |
| 🌐 **Wiki Oficial do Projeto** | [**GitHub Wiki**](https://github.com/rodrigothoma/sgopi-sentinela/wiki) | Base de conhecimento da equipe com guias, modelagem UML navegável e detalhamento arquitetural. |
| 📊 **Artefatos e Diagramas** | [**docs/diagramas/**](docs/diagramas/) | Todos os diagramas UML em alta definição (Casos de Uso, Pacotes, Componentes Executável e Hexagonal, Classes de Domínio, Implantação e Sequência). |

---

## 🎯 Proposta do MVP (Minimum Viable Product)

O MVP tem como objetivo validar o fluxo crítico e reativo do sistema de ponta a ponta:

```
[ Agente Policial ] ──(Registro)──► [ Núcleo SGOPI ] ◄──(Revisão/Validação)── [ Delegado ]
                                            │
                                            ▼ (Status: Validada)
[ Viatura Policial ] ◄──(Despacho)── [ Operador Central (Mapa Tático GPS Real-Time) ]
```

### Matriz de Priorização (MoSCoW)
- **Must Have (MVP Essencial):** RF01 (Gestão de Ocorrência Policial), RF04 (Fluxo de Validação pelo Delegado), RF02 (Monitoramento GPS e Despacho Tático).
- **Should Have (Alta Prioridade):** RF03 (Inventário de Apreensões), RF05 (Manchas Criminais e Alertas), RF07 (Laudos Periciais).
- **Could Have (Média Prioridade):** RF06 (Vinculação a Inquéritos), RF08 (Autenticação Pública de Documentos), RF09 (Medidas Protetivas).
- **Won't Have (Próximos Ciclos):** RF10 (Comunicação Interagências).

---

## 🏛️ Arquitetura do Software (Ports & Adapters)

O projeto adota a **Arquitetura Hexagonal** para garantir o isolamento estrito das regras de negócio de domínio:

* **Core Domain & Use Cases:** Regras de negócio puras (entidades e casos de uso) independentes de frameworks e bibliotecas externas (**RNF05**).
* **Inbound Ports & Adapters:** Endpoints REST e WebSockets reativos para atualização contínua do mapa tático sem recarregar a tela (**RNF01**).
* **Outbound Ports & Adapters:** Repositórios de persistência relacional (PostgreSQL), adaptadores de telemetria GPS com rotinas de contingência/fallback (**RNF04**), logs de auditoria imutáveis (**RNF03**) e controle de acesso RBAC (**RNF02**).

---

## 💻 Stack Tecnológica e Ferramentas

Para garantir a viabilidade técnica do MVP e o alinhamento com a Arquitetura Hexagonal, a infraestrutura e as ferramentas de desenvolvimento foram padronizadas conforme abaixo:

* **Linguagem e Framework Base (Backend):** Java (versão 21+) aliado ao Spring Boot 3. O Spring será restrito às camadas de adaptadores e inicialização (Inversão de Controle), garantindo que o *Core Domain* permaneça em Java puro, sem anotações de framework.
* **Gestão de Dependências e Build:** A automação da compilação e a gestão de bibliotecas serão conduzidas via Maven ou Gradle, assegurando a padronização do empacotamento (artefatos executáveis) para todos os membros da equipe.
* **Persistência de Dados (Outbound Adapters):** PostgreSQL como Sistema Gerenciador de Banco de Dados Relacional (SGBDR), manipulado no código através de Spring Data JPA e Hibernate.
* **Interface Gráfica e Tempo Real (Frontend):** 
  * *Painel Tático:* Renderização do mapa via biblioteca Leaflet conectada aos tiles do OpenStreetMap.
  * *Comunicação:* Reativa bidirecional viabilizada via WebSockets (STOMP/SockJS) para atualização das viaturas no mapa sem *refresh*.
* **Simulador de Telemetria GPS:** Script auxiliar independente (podendo ser desenvolvido em Python) que atuará como cliente, disparando requisições assíncronas periódicas para simular o deslocamento de viaturas e alimentar as portas de entrada do sistema.

---

## ⚙️ Estratégia de Qualidade e Gestão de Configuração

A garantia de qualidade e o fluxo de trabalho colaborativo são pilares para o sucesso no desenvolvimento do software, minimizando falhas de integração durante a disciplina.

### Abordagem de Testes (QA)
A validação do software ocorrerá em dois níveis distintos para isolar regras de negócio e testar a estabilidade da interface:
* **Testes de Unidade e Integração (Backend):** O foco central da cobertura de testes (meta superior a 80%) será a camada de Casos de Uso e Entidades de Domínio. Utilizando ferramentas como JUnit e Mockito, a máquina de estados das ocorrências e a geração do número de protocolo serão validadas de forma isolada, sem subir o contexto do servidor web ou do banco de dados relacional.
* **Testes Automatizados (E2E / Frontend):** Para garantir que os fluxos críticos funcionem de ponta a ponta na visão do usuário, serão implementados scripts de automação *black-box* utilizando o **Selenium WebDriver**. Essa automação validará cenários vitais, como o preenchimento correto dos formulários de registro circunstanciado (UC01), simulando o comportamento real do Agente Policial no navegador.

### Versionamento e Fluxo de Trabalho (Git Workflow)
Para orquestrar o desenvolvimento em equipe e proteger a estabilidade do código principal, o repositório adotará uma estratégia estruturada de ramificação:
* **Branches Principais:** 
  * `main`: Contém exclusivamente o código estável, testado e pronto para implantação.
  * `dev`: Branch de integração contínua onde as funcionalidades do MVP são unificadas e homologadas.
* **Gestão de Ambientes:** O projeto fará uso rigoroso do isolamento de ambientes e dependências (arquivos de propriedades locais e variáveis de ambiente) para garantir que a aplicação compile e execute perfeitamente nas máquinas de todos os desenvolvedores envolvidos, sem conflitos de portas ou configurações fixas.

---

## 📐 Modelagem e Artefatos de Projeto

A modelagem visual está organizada e disponível na documentação técnica e na Wiki:

* **Diagrama de Casos de Uso:** Mapeamento de todos os atores e fronteiras funcionais do ecossistema policial.
* **Diagrama de Pacotes:** Organização em camadas concêntricas (*domain*, *application*, *ports*, *adapters*).
* **Diagramas de Componentes:** 
  1. *Versão Executável (Build/Deploy):* Arquivos, empacotamento e artefatos de compilação.
  2. *Módulos Lógicos na Arquitetura Hexagonal:* Componentes de software e acoplamento via portas e adaptadores.
* **Diagrama de Classes de Domínio:** Entidades, atributos, métodos invariantes e relacionamentos.
* **Diagramas de Sequência (sq01 a sq11):** Interações dinâmicas e troca de mensagens para cada caso de uso.
* **Diagrama de Implantação:** Topologia física dos servidores, mensageria, banco de dados e clientes.

👉 Para visualizar todos os diagramas e suas especificações completas, acesse a [**Documentação de Engenharia**](docs/DOCUMENTACAO_DE_ENGENHARIA.md) ou a [**Wiki do Projeto**](https://github.com/rodrigothoma/sgopi-sentinela/wiki/Modelagem-UML).

---

## 👥 Equipe de Desenvolvimento

* **Fade Hassan Husein Kanaan**
* **Gabriel Ortiz**
* **Gustavo Fernandes dos Anjos**
* **Mateus Estivalet Valau**
* **Matheus Cabral**
* **Rodrigo Thoma da Silva**

### 🎓 Corpo Docente / Orientação
* **Prof. Dr. Fabio Paulo Basso**
* **Prof. Dr. Gilleanes Thorwald Araujo Guedes**
