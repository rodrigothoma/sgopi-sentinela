#!/usr/bin/env python3
"""
Script de automação para cadastro completo de issues e vinculação ao Kanban do GitHub Projects.
Repositório: rodrigothoma/sgopi-sentinela
Project: SGOPI Sentinela (Project #2 / PVT_kwHODOCzfM4BhrF5)
"""
import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error

parser = argparse.ArgumentParser(description="Cadastro de issues e Kanban no GitHub Projects")
parser.add_argument("--token", help="GitHub Personal Access Token (PAT)")
args, _ = parser.parse_known_args()

TOKEN = args.token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN", "")
REPO = "rodrigothoma/sgopi-sentinela"
PROJECT_ID = "PVT_kwHODOCzfM4BhrF5"
STATUS_FIELD_ID = "PVTSSF_lAHODOCzfM4BhrF5zhgl98Q"

STATUS_OPTIONS = {
    "Backlog": "f75ad846",
    "Sprint Backlog": "61e4505c",
    "In progress": "47fc9ee4",
    "In review": "df73e18b",
    "Done": "98236657"
}

MILESTONES = [
    {"title": "M1: Identidade Visual, Tema Claro/Escuro & Acessibilidade", "description": "Fundação visual, paleta reversa de alto contraste, logo e acessibilidade."},
    {"title": "M2: Portal Sentinela Cidadão (Delegacia Eletrônica)", "description": "Landing page pública, registro simplificado com mapa e consulta de protocolo."},
    {"title": "M3: Módulo Operacional & Policial (Área Restrita)", "description": "Sidebar moderna, RBAC, fila do delegado e formalização técnica do agente."},
    {"title": "M4: Centro de Comando Tático, Despacho & Inteligência", "description": "Painel GPS tempo real, proximidade Haversine, frota, manchas criminais e apreensões."},
    {"title": "M5: Auditoria, Conformidade & Segurança", "description": "Trilha de auditoria imutável, hash SHA-256 e mascaramento de dados sensíveis."},
    {"title": "M6: Qualidade, Testes E2E, Integração & Apresentação", "description": "Testes ponta a ponta, cobertura >= 80%, documentação alinhada e ensaio final."},
]

LABELS_CONFIG = [
    {"name": "frontend", "color": "1d76db", "description": "Interface web React / Vite"},
    {"name": "backend", "color": "006b75", "description": "API FastAPI e Arquitetura Hexagonal"},
    {"name": "ui/ux", "color": "d4c5f9", "description": "Design visual, tema e experiência do usuário"},
    {"name": "feature", "color": "a2eeef", "description": "Nova funcionalidade"},
    {"name": "enhancement", "color": "84b6eb", "description": "Refatoração e melhoria"},
    {"name": "security", "color": "e11d48", "description": "Autenticação, auditoria e conformidade"},
    {"name": "qa", "color": "fbca04", "description": "Testes e qualidade de software"},
    {"name": "documentation", "color": "0075ca", "description": "Documentação técnica, UML e Wiki"},
    {"name": "websocket", "color": "d93f0b", "description": "Comunicação em tempo real"},
]

ISSUES = [
    # --- MILESTONE 1 ---
    {
        "milestone": "M1: Identidade Visual, Tema Claro/Escuro & Acessibilidade",
        "title": "Implementação do ThemeProvider com Suporte a Tema Claro/Escuro Reverso",
        "labels": ["frontend", "ui/ux", "enhancement"],
        "status": "Done",
        "body": """### Objetivo
Garantir suporte rigoroso e simétrico a temas claro e escuro em toda a aplicação SGOPI Sentinela, adotando padrão de cores reversas de alto contraste.

### Contexto & Regras de Engenharia
- O sistema precisa manter contraste nítido em salas de operações (tema escuro) e em escritórios iluminados (tema claro).
- Variáveis semânticas em `styles.css` com inversão de base: `--bg`, `--card`, `--ink`, `--muted`, `--line`, `--primary`.

### Tarefas Realizadas / Critérios de Aceitação
- [x] Criado `ThemeContext` e hook `useTheme()` com persistência em `localStorage`.
- [x] Detecção automática da preferência do sistema operacional via `prefers-color-scheme`.
- [x] Botão alternador de tema com ícones interativos ☀️ / 🌙 presente na Navbar pública, no Login e no AppShell.
- [x] Atendimento a contraste mínimo WCAG AA em ambos os modos.
"""
    },
    {
        "milestone": "M1: Identidade Visual, Tema Claro/Escuro & Acessibilidade",
        "title": "Integração da Logo Oficial SVG do SGOPI Sentinela",
        "labels": ["frontend", "ui/ux"],
        "status": "Done",
        "body": """### Objetivo
Integrar a identidade visual definitiva do SGOPI Sentinela através de vetor SVG com brasão distintivo, estrela central e tipografia curvada.

### Contexto & Regras de Engenharia
- A logo vetorial em `images/logo.svg` utiliza `fill="currentColor"`, permitindo herança dinâmica de cores nos temas.

### Tarefas Realizadas / Critérios de Aceitação
- [x] Logo copiada para `frontend/public/logo.svg`.
- [x] Criado componente reutilizável `LogoSgopi.tsx` com controle de tamanho e cor.
- [x] Integrada na Navbar pública, no card de login central e no topo do painel interno.
- [x] Favicon da aba do navegador configurado.
"""
    },
    {
        "milestone": "M1: Identidade Visual, Tema Claro/Escuro & Acessibilidade",
        "title": "Integração do Componente SplitFlapText (React Bits)",
        "labels": ["frontend", "ui/ux"],
        "status": "Done",
        "body": """### Objetivo
Incorporar o componente de display mecânico de aletas (SplitFlapText) no cabeçalho do portal para dinamismo visual na chegada do usuário.

### Contexto & Regras de Engenharia
- O componente foi adaptado para respeitar as variáveis de tema e renderizar texto nítido no escuro e no claro.
- Suporte a acessibilidade através de `prefers-reduced-motion` e atributos ARIA.

### Tarefas Realizadas / Critérios de Aceitação
- [x] Componente `SplitFlapText.tsx` e `SplitFlapText.css` criados em `src/components/common/`.
- [x] Alternância cíclica de mensagens de segurança pública ('SENTINELA ONLINE', 'PORTAL CIDADÃO', 'PRONTIDÃO TOTAL').
- [x] Suporte a redução de movimento desativando animações quando solicitado pelo sistema.
"""
    },
    {
        "milestone": "M1: Identidade Visual, Tema Claro/Escuro & Acessibilidade",
        "title": "Expansão dos Dicionários i18n para Portal Público e Termos Técnicos",
        "labels": ["frontend", "enhancement"],
        "status": "Done",
        "body": """### Objetivo
Garantir internacionalização completa (Português do Brasil e Inglês) para todas as interfaces do portal do cidadão, formulários e painéis policiais.

### Contexto & Regras de Engenharia
- Arquivos em `public/locales/pt/common.json` e `public/locales/en/common.json`.

### Tarefas Realizadas / Critérios de Aceitação
- [x] Seletor de idioma na Navbar e tela de login com atualização reativa sem recarregar a página.
- [x] Dicionários cobrindo ações, status, papéis, avisos e termos do portal do cidadão.
- [x] Persistência da preferência de idioma no navegador.
"""
    },

    # --- MILESTONE 2 ---
    {
        "milestone": "M2: Portal Sentinela Cidadão (Delegacia Eletrônica)",
        "title": "Construir Landing Page Pública com Hero e Cards de Ação",
        "labels": ["frontend", "feature"],
        "status": "Done",
        "body": """### Objetivo
Criar a página inicial pública (`/`) para que o cidadão e a sociedade tenham acesso imediato aos serviços da corporação sem exigência prévia de login.

### Contexto & Regras de Engenharia
- A rota `/` não deve redirecionar de forma cega para `/login`.
- Deve apresentar de forma limpa as opções de Registrar Ocorrência, Consultar Protocolo e Acesso Policial.

### Tarefas Realizadas / Critérios de Aceitação
- [x] Rota `/` configurada para renderizar `LandingPage.tsx`.
- [x] Hero com SplitFlapText, logo oficial e subtítulo explicativo.
- [x] 3 cartões de ação rápida com efeitos de elevação suave e ícones semânticos.
- [x] Responsividade completa em mobile e desktop.
"""
    },
    {
        "milestone": "M2: Portal Sentinela Cidadão (Delegacia Eletrônica)",
        "title": "Desenvolver Formulário Simplificado de Registro Cidadão com Mapa Interativo",
        "labels": ["frontend", "feature"],
        "status": "Done",
        "body": """### Objetivo
Permitir que a população registre ocorrências (furtos, extravios, acidentes, perturbação) de forma ágil, com mapa Leaflet para fixar a coordenada exata.

### Contexto & Regras de Engenharia
- Rota pública `/registrar-cidadao`.
- Comunicação direta com a API pública sem envio de token JWT.
- Emissão do número de protocolo oficial `SGOPI-AAAA-NNNNNN`.

### Tarefas Realizadas / Critérios de Aceitação
- [x] Página `RegistroCidadaoPage.tsx` com formulário dividido em blocos claros.
- [x] Seletor de mapa Leaflet integrado para escolha intuitiva de latitude/longitude com pin.
- [x] Validação em tempo real (mínimo de 20 caracteres no relato conforme regra do domínio).
- [x] Tela de sucesso com comprovante, código de protocolo oficial e botão para copiar.
"""
    },
    {
        "milestone": "M2: Portal Sentinela Cidadão (Delegacia Eletrônica)",
        "title": "Implementar Consulta Pública de Ocorrência por Protocolo e Linha do Tempo",
        "labels": ["frontend", "feature"],
        "status": "Done",
        "body": """### Objetivo
Disponibilizar ao comunicante o acompanhamento da tramitação de sua ocorrência pelo número de protocolo em tempo real.

### Contexto & Regras de Engenharia
- Rota pública `/consulta` suportando leitura de parâmetro via URL `?protocolo=...`.
- Proteção da privacidade (RNF02): não expor dados sigilosos ou qualificações sensíveis.

### Tarefas Realizadas / Critérios de Aceitação
- [x] Tela `ConsultaProtocoloPage.tsx` com campo de entrada formatado.
- [x] Linha do tempo visual de 4 etapas (Triagem -> Validada -> Em Atendimento -> Finalizada).
- [x] Tratamento de erros amigável para protocolos inexistentes (404).
"""
    },
    {
        "milestone": "M2: Portal Sentinela Cidadão (Delegacia Eletrônica)",
        "title": "Endpoints de Ingestão Pública e Consulta de Protocolo no Backend Hexagonal",
        "labels": ["backend", "api", "security"],
        "status": "Done",
        "body": """### Objetivo
Adicionar endpoints REST seguros para recepção do registro público e consulta de protocolo, mantendo o isolamento do domínio.

### Contexto & Regras de Engenharia
- Adicionado ao `ocorrencias_router.py`: `POST /v1/ocorrencias/publico` e `GET /v1/ocorrencias/publico/{protocolo}`.
- O agregado `Ocorrencia` do domínio e suas invariantes são reutilizados integralmente sem quebras.

### Tarefas Realizadas / Critérios de Aceitação
- [x] Endpoint `POST /v1/ocorrencias/publico` gera protocolo no formato padrão `SGOPI-AAAA-NNNNNN`.
- [x] Endpoint `GET /v1/ocorrencias/publico/{protocolo}` retorna status e dados públicos.
- [x] 258 testes do backend continuam verdes (`uv run pytest -q`).
- [x] Contratos do `import-linter` 100% mantidos.
"""
    },
    {
        "milestone": "M2: Portal Sentinela Cidadão (Delegacia Eletrônica)",
        "title": "Módulo de Autenticação e Validação Pública de Documentos Policiais com QR Code (RF08)",
        "labels": ["frontend", "backend", "feature"],
        "status": "Sprint Backlog",
        "body": """### Objetivo
Implementar funcionalidade pública para validação de autenticidade de Boletins de Ocorrência e certidões via QR Code ou hash de verificação (RF08 / Could Have).

### Contexto & Regras de Engenharia
- Permite que órgãos judiciais, seguradoras e cidadãos validem a integridade do documento policial impresso ou em PDF.
- A validação confronta a chave pública do documento contra o hash SHA-256 armazenado no banco.

### Critérios de Aceitação
- [ ] Geração de QR Code legível nos comprovantes de ocorrência.
- [ ] Página pública `/autenticar` que valida a chave e certifica autenticidade.
- [ ] Indicador de 'DOCUMENTO AUTÊNTICO' ou 'NÃO RECONHECIDO'.
"""
    },

    # --- MILESTONE 3 ---
    {
        "milestone": "M3: Módulo Operacional & Policial (Área Restrita)",
        "title": "Redesenhar Layout AppShell com Sidebar Lateral Retrátil e User Pill",
        "labels": ["frontend", "ui/ux", "enhancement"],
        "status": "Sprint Backlog",
        "body": """### Objetivo
Transformar o layout interno do sistema operacional policial em uma experiência profissional com menu lateral retrátil e controle de perfil de usuário.

### Contexto & Regras de Engenharia
- O AppShell atual possui apenas uma barra superior simples. A sidebar moderna otimiza a área de tela para o mapa tático e tabelas de revisão.

### Critérios de Aceitação
- [ ] Sidebar colapsável com ícones e rótulos contextuais.
- [ ] Filtragem rigorosa de itens de menu pelo papel RBAC do usuário autenticado (Agente, Delegado, Operador).
- [ ] User Pill com indicação visual de patente/cargo e botão de logout seguro.
- [ ] Totalmente integrada ao sistema de tema claro/escuro.
"""
    },
    {
        "milestone": "M3: Módulo Operacional & Policial (Área Restrita)",
        "title": "Redesenhar Tela de Login com Identidade Visual e Atalhos de Demonstração (Seed)",
        "labels": ["frontend", "ui/ux"],
        "status": "Done",
        "body": """### Objetivo
Criar tela de login centralizada, moderna, com a logo oficial e facilidades para a banca de avaliação acadêmica e testes rápidos da equipe.

### Contexto & Regras de Engenharia
- Rota `/login` com card moderno, link de volta para a página inicial e seletores de tema.

### Tarefas Realizadas / Critérios de Aceitação
- [x] Tela `LoginPage.tsx` redesenhada com card central e logo SGOPI.
- [x] Botões 'Demo' de 1 clique para preenchimento de Agente, Delegada e Operador.
- [x] Mensagens de erro com suporte a i18n em caso de falha de autenticação.
- [x] Link de retorno visível ao portal público do cidadão.
"""
    },
    {
        "milestone": "M3: Módulo Operacional & Policial (Área Restrita)",
        "title": "Fila de Triagem do Delegado com Distinção de Origem (Cidadão vs Agente) (UC04 / RF04)",
        "labels": ["frontend", "feature"],
        "status": "Sprint Backlog",
        "body": """### Objetivo
Aprimorar a tela de revisão do Delegado (`/fila`) permitindo triar com facilidade ocorrências enviadas por cidadãos via web e registradas por agentes de campo.

### Contexto & Regras de Engenharia
- Ocorrências originadas pelo cidadão devem ter destaque visual (badge 'Web Cidadão').
- Ações: Validar (gera hash SHA-256), Devolver para Correção e Rejeitar (com justificativa obrigatória >= 10 chars).

### Critérios de Aceitação
- [ ] Filtro por origem da ocorrência (Todas, Web Cidadão, Agente Policial).
- [ ] Modal de rejeição/devolução com validação de justificativa.
- [ ] Atualização instantânea da fila após decisão do Delegado.
"""
    },
    {
        "milestone": "M3: Módulo Operacional & Policial (Área Restrita)",
        "title": "Redesign do Formulário Circunstanciado do Agente (RF01 / UC01)",
        "labels": ["frontend", "feature"],
        "status": "Sprint Backlog",
        "body": """### Objetivo
Modernizar a interface de registro técnico de ocorrência utilizada pelo policial em delegacia (`/registrar`).

### Contexto & Regras de Engenharia
- Suporte a múltiplos envolvidos qualificados (Vítima, Testemunha, Suspeito com documento e validação de CPF).
- Múltiplas tipificações penais (Artigo do Código Penal + descrição).
- Mapa georreferenciado e anexação permanente de evidências digitais.

### Critérios de Aceitação
- [ ] Adição dinâmica de múltiplos envolvidos e tipificações em cartões visuais limpos.
- [ ] Mapa Leaflet responsivo integrado ao seletor de coordenadas.
- [ ] Upload de evidências (PDF, PNG, JPG) com validação de tamanho e tipo.
"""
    },
    {
        "milestone": "M3: Módulo Operacional & Policial (Área Restrita)",
        "title": "Gestão da Cadeia de Custódia e Evidências Digitais com Hash SHA-256 (RF01 / RF22)",
        "labels": ["frontend", "backend", "security"],
        "status": "Backlog",
        "body": """### Objetivo
Garantir a visualização, conferência de integridade e download seguro de arquivos e evidências digitais anexados à ocorrência.

### Contexto & Regras de Engenharia
- Cada arquivo anexado gera metadados imutáveis (`EvidenciaModel`) e hash SHA-256 de 64 caracteres hexadecimais (RNF03).

### Critérios de Aceitação
- [ ] Galeria/lista de evidências no detalhe da ocorrência com nome, tamanho, data de envio e hash.
- [ ] Botão para download seguro com validação de autorização.
- [ ] Indicador de integridade criptográfica do arquivo armazenado.
"""
    },

    # --- MILESTONE 4 ---
    {
        "milestone": "M4: Centro de Comando Tático, Despacho & Inteligência",
        "title": "Redesign do Painel Tático GPS com Tiles Claro/Escuro e WebSockets em Tempo Real (RF02 / RNF01)",
        "labels": ["frontend", "feature", "websocket"],
        "status": "Sprint Backlog",
        "body": """### Objetivo
Refinar o painel com mapa tático interativo (`/painel`) para monitoramento de viaturas e ocorrências com latência visual abaixo de 1 segundo.

### Contexto & Regras de Engenharia
- Tiles de mapa adaptados dinamicamente para modo escuro (CartoDB Dark) e modo claro (OpenStreetMap padrão).
- Canal WebSocket `/v1/tempo-real` transmitindo telemetria e atualizações de status.

### Critérios de Aceitação
- [ ] Viaturas movem-se no mapa suavemente conforme coordenadas de telemetria recebidas via WS.
- [ ] Marcadores com diferenciação clara entre viaturas disponíveis, em deslocamento e ocupadas.
- [ ] Indicador de status da conexão WebSocket (Conectado / Reconectando / Offline).
"""
    },
    {
        "milestone": "M4: Centro de Comando Tático, Despacho & Inteligência",
        "title": "Despacho Tático de Viaturas com Sugestão por Proximidade Haversine (RF02 / UC02)",
        "labels": ["frontend", "backend", "feature"],
        "status": "Sprint Backlog",
        "body": """### Objetivo
Permitir ao operador da central despachar a viatura ideal para uma ocorrência validada, com ordenação automática por menor distância geográfica.

### Contexto & Regras de Engenharia
- Algoritmo de Haversine no domínio (`domain/despacho/servico_proximidade.py`).
- A confirmação gera `OrdemDeDespacho` e altera o status da viatura para `EM_DESLOCAMENTO` e da ocorrência para `EM_ATENDIMENTO`.

### Critérios de Aceitação
- [ ] Selecionar uma ocorrência no painel exibe as 3 viaturas disponíveis mais próximas com distância em km.
- [ ] Botão 'Confirmar Despacho' gera ordem e dispara evento reativo para os outros painéis.
- [ ] Modal de encerramento de ocorrência com desfecho circunstanciado.
"""
    },
    {
        "milestone": "M4: Centro de Comando Tático, Despacho & Inteligência",
        "title": "Gestão de Frota, Situações Operacionais e Controle do Simulador GPS (RF15 / RF16)",
        "labels": ["frontend", "feature"],
        "status": "Sprint Backlog",
        "body": """### Objetivo
Aprimorar a tela de frota (`/frota`) para controle de veículos, motoristas, manutenção e disparador do simulador de telemetria.

### Contexto & Regras de Engenharia
- Permite ao operador ligar/desligar o gerador de posições GPS simuladas para apresentação do MVP sem depender de rastreadores físicos.

### Critérios de Aceitação
- [ ] Tabela/grid de viaturas com status e situação operacional (Disponível, Em Deslocamento, Em Manutenção).
- [ ] Botão de alternância do simulador de GPS com feedback visual de telemetria ativa.
- [ ] Formulário de cadastro de nova viatura com placa e prefixo corporativo.
"""
    },
    {
        "milestone": "M4: Centro de Comando Tático, Despacho & Inteligência",
        "title": "Módulo de Manchas Criminais (Heatmap de Incidência Delitiva) e Alertas de Criticidade (RF05)",
        "labels": ["frontend", "backend", "feature"],
        "status": "Backlog",
        "body": """### Objetivo
Implementar a visualização geográfica em mapa de calor (manchas criminais) baseada na densidade de ocorrências por região (RF05 / Should Have).

### Contexto & Regras de Engenharia
- Renderização de camada heatmap sobre Leaflet com dados agregados por período (últimos 7 dias, 30 dias).
- Alerta visual de alta criticidade quando houver concentração atípica de delitos em uma área geográfica num intervalo de 24 horas.

### Critérios de Aceitação
- [ ] Camada de heatmap ativável/desativável no painel tático.
- [ ] Filtro por natureza de crime (ex: somente furtos, somente roubos).
- [ ] Banner de alerta de criticidade disparado para operadores e supervisores.
"""
    },
    {
        "milestone": "M4: Centro de Comando Tático, Despacho & Inteligência",
        "title": "Gestão de Inventário de Apreensões Vinculado a Ocorrências (RF03 / UC03)",
        "labels": ["frontend", "backend", "feature"],
        "status": "Backlog",
        "body": """### Objetivo
Implementar o registro formal de armas, drogas, veículos e objetos apreendidos em ocorrências, garantindo cadeia de custódia (RF03 / Should Have).

### Contexto & Regras de Engenharia
- Todo item apreendido possui número de série/lacre, descrição e vínculo unívoco à ocorrência de origem.

### Critérios de Aceitação
- [ ] Aba de apreensões no detalhe da ocorrência.
- [ ] Cadastro com tipo de item, quantidade, estado de conservação e localização no depósito/cofre.
- [ ] Emissão do Auto de Apreensão em formato imprimível.
"""
    },

    # --- MILESTONE 5 ---
    {
        "milestone": "M5: Auditoria, Conformidade & Segurança",
        "title": "Painel de Trilha de Auditoria Imutável e Logs com Máscara de CPF (RNF02 / RNF03 / RF20)",
        "labels": ["frontend", "backend", "security"],
        "status": "Backlog",
        "body": """### Objetivo
Criar tela de consulta exclusiva para o Supervisor/Auditor para visualização de todos os eventos sensíveis do sistema.

### Contexto & Regras de Engenharia
- Tabela `registros_auditoria` imutável (append-only) gravando autor, IP, ação, entidade afetada e justificativas.
- Mascaramento rigoroso de CPF (ex: `***.456.789-**`) nos logs JSON e na interface pública para conformidade com a LGPD.

### Critérios de Aceitação
- [ ] Tela de visualização de logs de auditoria com filtro por data, ator e tipo de operação.
- [ ] Nenhuma linha de auditoria pode ser editada ou removida via API.
- [ ] Máscara de dados sensíveis ativa em todas as saídas de log.
"""
    },
    {
        "milestone": "M5: Auditoria, Conformidade & Segurança",
        "title": "Validação Criptográfica de Narrativa Policial (DEC-09 / Hash SHA-256)",
        "labels": ["backend", "security"],
        "status": "Done",
        "body": """### Objetivo
Garantir o princípio de não repúdio e imutabilidade da narrativa policial após a validação pelo Delegado.

### Contexto & Regras de Engenharia
- Ao validar a ocorrência, o sistema gera o hash SHA-256 da narrativa (`hash_narrativa`).
- Em qualquer consulta subsequente, o hash é recalculado para verificar se o texto permaneceu íntegro (`narrativa_integra: true`).

### Tarefas Realizadas / Critérios de Aceitação
- [x] Implementado no agregado `Ocorrencia.validar(...)`.
- [x] Persistência do hash na coluna `hash_narrativa` do PostgreSQL.
- [x] Cobertura em testes unitários do domínio validando divergência de hash em caso de adulteração.
"""
    },

    # --- MILESTONE 6 ---
    {
        "milestone": "M6: Qualidade, Testes E2E, Integração & Apresentação",
        "title": "Automação de Testes E2E do Fluxo Ponta a Ponta (Registro Cidadão ao Despacho)",
        "labels": ["qa", "testing"],
        "status": "Sprint Backlog",
        "body": """### Objetivo
Automatizar a validação end-to-end simulando a jornada completa no navegador: registro pelo cidadão -> validação pelo delegado -> despacho pelo operador.

### Contexto & Regras de Engenharia
- Utilizar Playwright ou Cypress cobrindo os cenários críticos do sistema.

### Critérios de Aceitação
- [ ] Teste preenche o formulário público do cidadão e verifica recebimento do protocolo.
- [ ] Teste autentica como Delegada, aprova a ocorrência e verifica transição de status.
- [ ] Teste autentica como Operador e confirma despacho da viatura mais próxima.
"""
    },
    {
        "milestone": "M6: Qualidade, Testes E2E, Integração & Apresentação",
        "title": "Manutenção da Cobertura de Testes Unitários e Integração (>= 80% Core)",
        "labels": ["qa", "backend"],
        "status": "Done",
        "body": """### Objetivo
Assegurar alta confiabilidade do backend com suíte de testes contínua sobre o domínio e portas de aplicação (RNF06).

### Contexto & Regras de Engenharia
- Executado via `uv run pytest --cov`.
- Testes sem banco externo usando Fakes de portas em `tests/fakes/` e SQLite em memória.

### Tarefas Realizadas / Critérios de Aceitação
- [x] 258 testes passando com 100% de sucesso.
- [x] Cobertura superior a 90% sobre `domain/` e `application/`.
- [x] Execução rápida abaixo de 10 segundos para todo o conjunto.
"""
    },
    {
        "milestone": "M6: Qualidade, Testes E2E, Integração & Apresentação",
        "title": "Atualização Completa da Documentação de Engenharia e Wiki com Arquitetura Dual",
        "labels": ["documentation"],
        "status": "In progress",
        "body": """### Objetivo
Atualizar toda a documentação técnica acadêmica (`DOCUMENTACAO_DE_ENGENHARIA.md`, `README.md` e Wiki) refletindo a expansão da arquitetura dual (Portal Cidadão + Painel Policial).

### Contexto & Regras de Engenharia
- Adicionar casos de uso públicos ao catálogo de requisitos e diagrama geral.
- Documentar os novos endpoints REST, o sistema de temas reversos e a logo oficial.

### Critérios de Aceitação
- [ ] Diagrama de Casos de Uso atualizado contemplando o Cidadão como ator externo.
- [ ] Matriz MoSCoW e catálogo de requisitos atualizados com rastreabilidade total.
- [ ] README principal com novas capturas de tela e roteiro de execução.
"""
    },
    {
        "milestone": "M6: Qualidade, Testes E2E, Integração & Apresentação",
        "title": "Roteiro Consolidado de Demonstração, Seeds e Ensaio para a Banca Final",
        "labels": ["documentation", "qa"],
        "status": "Sprint Backlog",
        "body": """### Objetivo
Preparar o ambiente reproduzível e o roteiro cronometrado para a apresentação final aos professores avaliadores da Unipampa.

### Contexto & Regras de Engenharia
- Script `backend/scripts/seed.py` atualizado para carregar massa de dados de teste (usuários, viaturas e ocorrências de exemplo).

### Critérios de Aceitação
- [ ] Um comando (`uv run python -m scripts.seed`) deixa todo o sistema pronto para apresentação.
- [ ] Roteiro de demonstração de 10 minutos ensaiado entre os integrantes da equipe.
- [ ] Apresentação ao vivo fluida alternando entre portal do cidadão, delegado e central tática.
"""
    }
]


def req_api(metodo, endpoint, dados=None):
    url = f"https://api.github.com/repos/{REPO}{endpoint}"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "SGOPI-Full-Cadastre"
    }
    corpo = json.dumps(dados).encode("utf-8") if dados else None
    req = urllib.request.Request(url, data=corpo, headers=headers, method=metodo)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"Erro HTTP {e.code} em {endpoint}: {e.read().decode('utf-8')[:150]}")
        raise


def req_graphql(query, variables=None):
    url = "https://api.github.com/graphql"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "SGOPI-Full-Cadastre"
    }
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    corpo = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=corpo, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"Erro GraphQL: {e.read().decode('utf-8')[:150]}")
        raise


def main():
    print("=" * 60)
    print("  SGOPI SENTINELA — CADASTRO INTEGRAL DE ISSUES & KANBAN")
    print(f"  Repositório: {REPO}")
    print(f"  Projeto Kanban: {PROJECT_ID}")
    print(f"  Total de Novas Issues: {len(ISSUES)}")
    print("=" * 60)

    # 1. Carregar ou criar Milestones
    print("\n1. Sincronizando Milestones...")
    milestones_existentes = {}
    try:
        res = req_api("GET", "/milestones?state=all")
        for m in res:
            milestones_existentes[m["title"]] = m["number"]
    except Exception as e:
        print(f"Aviso ao buscar milestones: {e}")

    for m in MILESTONES:
        if m["title"] not in milestones_existentes:
            try:
                novo = req_api("POST", "/milestones", {"title": m["title"], "description": m["description"]})
                milestones_existentes[m["title"]] = novo["number"]
                print(f"  + Milestone criada: '{m['title']}' (#{novo['number']})")
            except Exception as e:
                print(f"  ! Erro ao criar milestone '{m['title']}': {e}")
        else:
            print(f"  = Milestone existente: '{m['title']}' (#{milestones_existentes[m['title']]})")

    # 2. Sincronizar Labels
    print("\n2. Sincronizando Labels...")
    for lb in LABELS_CONFIG:
        try:
            req_api("POST", "/labels", lb)
            print(f"  + Label criada: '{lb['name']}'")
        except Exception:
            # Já existe
            pass

    # 3. Cadastrar cada Issue e Adicionar ao Kanban Project #2
    print("\n3. Criando Issues e Vinculando ao Kanban...")
    sucessos = 0
    for idx, iss in enumerate(ISSUES, 1):
        num_milestone = milestones_existentes.get(iss["milestone"])
        payload = {
            "title": iss["title"],
            "body": iss["body"],
            "labels": iss["labels"]
        }
        if num_milestone:
            payload["milestone"] = num_milestone

        try:
            # A. Criar Issue no Repositório
            res_issue = req_api("POST", "/issues", payload)
            issue_num = res_issue["number"]
            issue_node_id = res_issue["node_id"]
            issue_url = res_issue["html_url"]
            print(f"\n[#{issue_num}] {iss['title']}")
            print(f"  Link: {issue_url}")

            # B. Adicionar Issue ao Project V2 (Kanban)
            mutation_add = """
            mutation AddItem($projectId: ID!, $contentId: ID!) {
              addProjectV2ItemById(input: {projectId: $projectId, contentId: $contentId}) {
                item {
                  id
                }
              }
            }
            """
            res_add = req_graphql(mutation_add, {"projectId": PROJECT_ID, "contentId": issue_node_id})
            item_id = res_add.get("data", {}).get("addProjectV2ItemById", {}).get("item", {}).get("id")

            # C. Definir Status da Coluna do Kanban
            status_nome = iss.get("status", "Backlog")
            status_opt_id = STATUS_OPTIONS.get(status_nome, STATUS_OPTIONS["Backlog"])

            if item_id:
                mutation_status = """
                mutation UpdateStatus($projectId: ID!, $itemId: ID!, $fieldId: ID!, $optionId: String!) {
                  updateProjectV2ItemFieldValue(input: {
                    projectId: $projectId,
                    itemId: $itemId,
                    fieldId: $fieldId,
                    value: {
                      singleSelectOptionId: $optionId
                    }
                  }) {
                    projectV2Item {
                      id
                    }
                  }
                }
                """
                req_graphql(mutation_status, {
                    "projectId": PROJECT_ID,
                    "itemId": item_id,
                    "fieldId": STATUS_FIELD_ID,
                    "optionId": status_opt_id
                })
                print(f"  Kanban Card: {item_id} -> Coluna: [{status_nome}]")

            sucessos += 1
            time.sleep(0.5)  # Evitar rate-limit secundário do GitHub
        except Exception as e:
            print(f"  ! Erro ao cadastrar issue '{iss['title']}': {e}")

    print(f"\n" + "=" * 60)
    print(f"  CONCLUÍDO COM SUCESSO!")
    print(f"  {sucessos}/{len(ISSUES)} issues criadas e vinculadas ao Kanban do Project #2.")
    print(f"  Acesse o quadro: https://github.com/users/rodrigothoma/projects/2")
    print("=" * 60)


if __name__ == "__main__":
    main()
