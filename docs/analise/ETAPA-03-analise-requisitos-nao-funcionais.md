# ETAPA 03 — Análise dos Requisitos Não Funcionais (RNF01–RNF05)

**Objetivo da etapa:** avaliar cada RNF quanto a mensurabilidade, completude e coerência com a arquitetura/stack, verificar como o código atual se comporta em relação a ele, e listar RNFs ausentes que já estão implícitos nos documentos ou no código.

Legenda: 🔴 bloqueante · 🟠 alto · 🟡 médio · ⚪ baixo

---

## 1. Avaliação por requisito

### RNF01 — Desempenho e Tempo Real

| ID | Sev. | Problema | Evidência | Recomendação |
| :--- | :---: | :--- | :--- | :--- |
| **RNF-P01** | 🟠 | **Não mensurável no próprio RNF.** "Latência mínima" só vira número no §3.4 (< 1 s). Não define carga (viaturas simultâneas, frequência de telemetria, usuários conectados). | RNF01, §3.4 | Reescrever com metas: latência p95 < 1 s da ingestão à renderização; ≥ 10 viaturas a 1 Hz; ≥ 5 painéis conectados (MVP em rede local). |
| **RNF-P02** | 🟠 | **"Mensageria assíncrona" sem tecnologia.** Nenhum broker (RabbitMQ/Redis/Kafka) aparece na stack (README §Stack), no `pyproject.toml` nem no diagrama de implantação. | README, implantação | No MVP: fila em memória (`asyncio.Queue`) atrás de uma **porta** `PublicadorEventos`; broker real fica como adapter futuro. Registrar essa decisão. |
| **RNF-P03** | 🟡 | Mistura três preocupações: manchas criminais (RF05, Should), telemetria (RF02) e despacho. O MVP só precisa das duas últimas. | RNF01 | Separar em RNF01.a (telemetria/despacho — MVP) e RNF01.b (processamento geoespacial — futuro). |

### RNF02 — Proteção e Controle de Acesso (RBAC)

| ID | Sev. | Problema | Evidência | Recomendação |
| :--- | :---: | :--- | :--- | :--- |
| **RNF-P04** | 🔴 | **Nada implementado.** Não há autenticação, autorização, usuário nem papel no código; ID do agente vem do cliente. Critério de aceite 2 do MVP depende disso. | DIV-20 | RF11/RF12 + RNF02 reescrito (Etapa 4). |
| **RNF-P05** | 🟠 | **Lista de papéis incompleta.** RNF02: Agente, Delegado, Perito, Operador de Central, Supervisor, Cidadão. Textos de UC citam também **Escrivão** (UC06) e **Analista de Inteligência** (UC05). Cidadão não é papel autenticado (UC08 é público). | DIV-06 | Fixar enum `Papel = {AGENTE, DELEGADO, OPERADOR_CENTRAL, SUPERVISOR, PERITO, ESCRIVAO}`; "Cidadão" = acesso anônimo. |
| **RNF-P06** | 🟠 | **Mecanismos não especificados:** tipo de credencial (senha? hash?), expiração de sessão (`.env` sugere JWT 24 h — longo para sistema policial), transporte (HTTPS), *rate limiting* (`DISABLE_REQUEST_LIMITS` existe no `.env` sem implementação), política de CORS. | `.env.example`, `main.py` | Especificar: senha com bcrypt/argon2; JWT 8 h (turno); HTTPS obrigatório fora de dev; CORS por lista de origens (corrigir DIV-25). |
| **RNF-P07** | 🟡 | **Privacidade só no portal público.** LGPD é citada apenas em UC08; não há regra para mascarar CPF/telefone em logs, respostas por papel, ou nos dados de teste (`seed.sql`). | UC08 regra 1 | Novo RNF de conformidade LGPD (RNF10 na Etapa 4). |

### RNF03 — Segurança, Imutabilidade e Auditoria

| ID | Sev. | Problema | Evidência | Recomendação |
| :--- | :---: | :--- | :--- | :--- |
| **RNF-P08** | 🟠 | **Mecanismo de "logs inalteráveis" não definido.** Tabela *append-only*? Hash encadeado? Assinatura? Quem pode ler? Não há entidade `RegistroAuditoria` no código nem porta `PortaAuditoria`. | Diagrama de pacotes cita `PortaAuditoria`; código não tem | Definir para o MVP: tabela `registros_auditoria` sem UPDATE/DELETE (revogar privilégios ao *role* da aplicação), campos `quem, quando, operacao, entidade, entidade_id, antes, depois`. |
| **RNF-P09** | 🟠 | **Esquema físico contradiz o RNF.** `cascade="all, delete-orphan"` e `ondelete="CASCADE"` nos models permitem exclusão em cascata de ocorrências e envolvidos. | DIV-24 | Remover cascatas de exclusão; não expor `DELETE` na API; usar *soft delete* auditado se necessário. |
| **RNF-P10** | 🟡 | **Sem versionamento nem rastro de alteração.** Nenhuma entidade tem `atualizada_em`, `versao` ou histórico. "Retificações auditadas" exigem isso. | `models.py` | Adicionar `atualizada_em`, `versao` (optimistic locking) e histórico de status (`historico_status`). |
| **RNF-P11** | 🟡 | **Tensão jurídica não endereçada.** "Não podem ser excluídos" × direito de eliminação da LGPD (art. 18). Há base legal (exercício regular de direitos / segurança pública), mas o documento deveria mencioná-la. | RNF03 | Nota de conformidade no RNF. |
| **RNF-P12** | 🟡 | "Documentos oficiais imutáveis" pressupõe emissão de documentos (não existe RF — DIV-14). | — | Reduzir escopo do RNF03 no MVP a: ocorrência validada, ordem de despacho e registros de auditoria. |

### RNF04 — Confiabilidade e Tolerância a Falhas

| ID | Sev. | Problema | Evidência | Recomendação |
| :--- | :---: | :--- | :--- | :--- |
| **RNF-P13** | 🟡 | **Bem redigido, mas parcial.** Cobre GPS, mapa e integrações; não cobre: queda do banco (o que a API responde?), queda do WebSocket (reconexão automática — está em D3, não no RNF), perda do simulador. | Planejamento D3 | Adicionar cenários: WS reconecta com *backoff*; `/health` reporta DB `down`; API responde 503 padronizado. |
| **RNF-P14** | 🟡 | **Retentativas sem parâmetros.** "Timeouts geram retentativas" — quantas? com que intervalo? UC12 diz "1 hora", UC10 diz "automáticas". | UC10, UC12 | Padrão: 3 tentativas, *backoff* exponencial (1 s, 4 s, 16 s), depois log e status `Pendente`. |
| **RNF-P15** | 🟡 | O limiar de "GPS desatualizado" (> 60 s) está no UC02, não no RNF04. | UC02 regra 3 | Mover para o RNF (parametrizável). |

### RNF05 — Manutenibilidade e Desacoplamento

| ID | Sev. | Problema | Evidência | Recomendação |
| :--- | :---: | :--- | :--- | :--- |
| **RNF-P16** | 🟡 | **Sem verificação automática.** A "regra de ouro" (domínio/aplicação sem libs externas) está só em texto. Nada impede um `import fastapi` em `domain/`. | README | Adicionar `import-linter` (ou teste que inspeciona `sys.modules`) como parte de RNF05 — ver RNF06. |
| **RNF-P17** | 🟡 | **Aderência parcial no código atual.** Adapter chama repositório sem caso de uso; DI resolve implementação concreta; domínio lança `ValueError`. | DIV-28, DIV-29 | Lista HEX-nn na Etapa 4. |
| **RNF-P18** | ⚪ | Cita "provedores de mapas" como dependência a isolar, mas o mapa é responsabilidade do **frontend** (Leaflet); o backend só entrega coordenadas. | RNF05 | Ajustar redação: isolar "telemetria, mensageria, armazenamento de arquivos e assinatura". |

---

## 2. Requisitos não funcionais **ausentes**

| # | RNF ausente | Onde já está implícito | Por que precisa existir | Proposta (Etapa 4) |
| :--- | :--- | :--- | :--- | :--- |
| B1 | **Testabilidade / cobertura** | README §Qualidade (≥ 80 %), Doc §7.1, Planejamento F3 | Meta declarada em três lugares sem ser requisito nem estar configurada (`pytest-cov` ausente) | **RNF06** |
| B2 | **Portabilidade / ambiente reproduzível** | Planejamento T1, Doc §7.2 "Gestão de Ambientes", README | "Um colega clona e sobe com um comando" é critério de aceite da Verificação 1 | **RNF07** |
| B3 | **Internacionalização (pt/en)** | **Já implementada** no backend (`infrastructure/i18n`) e no frontend (`react-i18next`) | Funcionalidade existente sem requisito que a justifique/limite | **RNF08** |
| B4 | **Observabilidade** (health com DB, logs estruturados, correlação de requisição) | Planejamento T1 (`/health` verificando banco); RNF04 ("logs de erro") | Sem isso a demo ao vivo não tem diagnóstico | **RNF09** |
| B5 | **Conformidade LGPD / privacidade** | UC08 regra 1; RNF02 | Sistema trata dados sensíveis (art. 5º, II) de vítimas e suspeitos | **RNF10** |
| B6 | **Integridade transacional / consistência** | §3.2 hipótese técnica ("sem comprometer a integridade transacional") | Despacho altera 3 agregados (ocorrência, viatura, ordem) — precisa ser atômico | **RNF11** |
| B7 | **Documentação de API** | FastAPI gera OpenAPI; Planejamento T5 ("Swagger em /docs") | Contrato entre frontend e backend (Princípio 03 do Planejamento) | **RNF12** |
| B8 | **Compatibilidade / usabilidade** (navegadores, resolução do painel tático) | Selenium (§7.1) pressupõe um navegador-alvo | Fora do MVP — registrado na Etapa 5 | — |
| B9 | **Disponibilidade / backup / retenção** | RNF03 ("imutabilidade") pressupõe retenção | Fora do MVP acadêmico — Etapa 5 | — |

---

## 3. Coerência RNF × Stack × Diagramas

| Tema | RNF diz | Stack/diagrama diz | Código faz | Veredito |
| :--- | :--- | :--- | :--- | :--- |
| Persistência | Relacional, imutável (RNF03) | PostgreSQL (README) **e** Firestore (§4.3) | PostgreSQL/SQLAlchemy | Corrigir §4.3 (DIV-01) |
| Tempo real | WebSockets + mensageria (RNF01) | WebSockets; STOMP/SockJS (§4.3) | Nada | Fixar "WebSocket nativo FastAPI" |
| RBAC | Papéis (RNF02) | `GatewaySegurança` (componentes); `Autenticacao.xml` (implantação) | Nada | Especificar JWT + dependência FastAPI |
| Auditoria | Logs inalteráveis (RNF03) | `PortaAuditoria`, `RegistroAuditoria` | Nada | Criar porta + adapter append-only |
| Resiliência | Fallbacks (RNF04) | — | Nada | OK para Sprint 4 |
| Desacoplamento | Hexagonal (RNF05) | Pacotes/componentes hexagonais | Parcial | Ver HEX-nn |

---

## O que foi feito nesta etapa

1. Cada RNF01–RNF05 avaliado quanto a mensurabilidade, completude, mecanismo e aderência do código; **18 problemas** registrados (`RNF-P01`…`RNF-P18`).
2. Identificados **9 RNFs ausentes** (B1–B9), dos quais 7 são propostos para o MVP na Etapa 4 e 2 ficam fora do escopo (Etapa 5).
3. Tabela de coerência RNF × stack × diagramas × código.
4. Nenhum documento original alterado.

**Próxima etapa:** consolidar os requisitos novos/reescritos e mapeá-los em portas, casos de uso e adaptadores (`ETAPA-04`).
