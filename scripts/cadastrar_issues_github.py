#!/usr/bin/env python3
"""
Script de automação para cadastro de issues e milestones no repositório GitHub do SGOPI Sentinela.
Uso:
    python3 scripts/cadastrar_issues_github.py --token <SEU_GITHUB_PAT>
ou:
    export GITHUB_TOKEN="<SEU_GITHUB_PAT>"
    python3 scripts/cadastrar_issues_github.py

Modo seco (apenas visualização das issues):
    python3 scripts/cadastrar_issues_github.py --dry-run
"""
import argparse
import json
import os
import sys
import urllib.request
import urllib.error

REPO = "rodrigothoma/sgopi-sentinela"

MILESTONES = [
    {"title": "M1: Identidade Visual, Tema Claro/Escuro & i18n", "description": "Fundação visual, cores reversas e acessibilidade."},
    {"title": "M2: Portal Sentinela Cidadão (Área Pública)", "description": "Landing page, registro simplificado e consulta por protocolo."},
    {"title": "M3: Backend & Ingestão Pública", "description": "Suporte a canal público e consulta segura no backend hexagonal."},
    {"title": "M4: Redesign da Área Restrita Policial", "description": "Sidebar retrátil, fila do delegado e painéis operacionais."},
    {"title": "M5: Qualidade, Testes & Documentação", "description": "Testes E2E, cobertura e alinhamento da documentação de engenharia."},
]

ISSUES = [
    # Milestone 1
    {
        "milestone": "M1: Identidade Visual, Tema Claro/Escuro & i18n",
        "title": "Implementar ThemeProvider com suporte a Tema Claro/Escuro Reverso",
        "labels": ["frontend", "ui/ux", "enhancement"],
        "body": """### Objetivo
Garantir suporte rigoroso e simétrico a temas claro e escuro em toda a interface do SGOPI Sentinela, com padrão de cores reversas de alto contraste.

### Escopo
- Criar `ThemeContext` e hook `useTheme()`.
- Suportar persistência em `localStorage` e detecção automática de `prefers-color-scheme`.
- Variáveis semânticas em `styles.css`: `--bg`, `--card`, `--ink`, `--muted`, `--line`, `--primary`.

### Critérios de Aceitação
- [ ] O usuário consegue alternar entre modo Claro e Escuro através de botão na interface.
- [ ] O tema selecionado permanece ativo após recarregar a página (F5).
- [ ] Contraste visual atende aos padrões de acessibilidade WCAG AA em ambos os modos.
- [ ] Sem quebras de layout ou textos ilegíveis nas telas principais.
"""
    },
    {
        "milestone": "M1: Identidade Visual, Tema Claro/Escuro & i18n",
        "title": "Integrar Logo Oficial SVG do SGOPI Sentinela e Favicon",
        "labels": ["frontend", "ui/ux", "good first issue"],
        "body": """### Objetivo
Adotar a identidade visual definitiva do projeto através da logo oficial em vetor SVG (distintivo com inscrição vazada SGOPI e estrela central).

### Escopo
- Criar componente `<LogoSgopi size={...} color={...} />`.
- Usar `fill="currentColor"` para que o brasão respeite a paleta do tema.
- Atualizar favicon do navegador e título da página.

### Critérios de Aceitação
- [ ] Componente renderiza o distintivo com nitidez vetorial em qualquer escala.
- [ ] A cor do brasão adapta-se dinamicamente ao tema ativo.
- [ ] Integrado na Navbar pública, na tela de Login e no AppShell operacional.
"""
    },
    {
        "milestone": "M1: Identidade Visual, Tema Claro/Escuro & i18n",
        "title": "Integrar Componente SplitFlapText (React Bits)",
        "labels": ["frontend", "ui/ux"],
        "body": """### Objetivo
Integrar o componente mecânico retrô de painel de partidas (SplitFlapText) no topo da aplicação para dinamismo visual na chegada do usuário.

### Escopo
- Integrar `SplitFlapText.tsx` e `SplitFlapText.css` da React Bits.
- Configurar suporte a tema claro e escuro nas plaquinhas mecânicas.
- Respeitar diretiva `prefers-reduced-motion` para usuários sensíveis a movimento.

### Critérios de Aceitação
- [ ] O componente alterna de forma suave entre as frases configuradas.
- [ ] Acessibilidade preservada com `aria-label` e fallback para movimento reduzido.
- [ ] Performance estável com `requestAnimationFrame` sem travamentos de thread.
"""
    },
    {
        "milestone": "M1: Identidade Visual, Tema Claro/Escuro & i18n",
        "title": "Expandir Dicionários i18n para Portal Público e Termos Policiais",
        "labels": ["frontend", "i18n", "good first issue"],
        "body": """### Objetivo
Oferecer suporte bilíngue completo (Português do Brasil e Inglês) para todas as interfaces do portal do cidadão e painel policial.

### Escopo
- Atualizar `public/locales/pt/common.json` e `en/common.json`.
- Adicionar chaves para landing page, formulário do cidadão, consulta de protocolo e erros.

### Critérios de Aceitação
- [ ] Alternância de idioma instantânea sem recarregar a página.
- [ ] Persistência da preferência em `localStorage`.
- [ ] Zero chaves não traduzidas ou textos soltos em 'hardcode'.
"""
    },

    # Milestone 2
    {
        "milestone": "M2: Portal Sentinela Cidadão (Área Pública)",
        "title": "Construir Landing Page Pública com SplitFlapText e Acesso Rápido",
        "labels": ["frontend", "feature"],
        "body": """### Objetivo
Criar a página inicial pública (`/`) para que o cidadão encontre imediatamente os serviços de segurança pública sem ser forçado a fazer login.

### Escopo
- Hero com componente `SplitFlapText` e logo SGOPI.
- Cards destacados para 'Registrar Ocorrência', 'Consultar Protocolo' e 'Acesso Policial'.
- Navbar pública com seletores de idioma e tema.

### Critérios de Aceitação
- [ ] A rota `/` renderiza a landing page pública sem redirecionar para `/login`.
- [ ] Design responsivo adaptado para desktop e smartphones.
- [ ] Botão de 'Acesso Policial' claramente visível para agentes e operadores.
"""
    },
    {
        "milestone": "M2: Portal Sentinela Cidadão (Área Pública)",
        "title": "Desenvolver Formulário Simplificado de Registro Cidadão (Delegacia Online)",
        "labels": ["frontend", "feature"],
        "body": """### Objetivo
Permitir que qualquer cidadão registre ocorrências como furto, extravio de documentos ou perturbação de forma ágil e amigável.

### Escopo
- Rota `/registrar-cidadao`.
- Formulário intuitivo: dados do comunicante, natureza, relato e endereço.
- Mapa Leaflet com pin clicável para registrar latitude e longitude exatas.
- Exibição de comprovante com número de protocolo `SGOPI-AAAA-NNNNNN` e botão para copiar.

### Critérios de Aceitação
- [ ] Validações amigáveis no frontend (mínimo 20 caracteres na descrição).
- [ ] Dispara envio para o endpoint público e exibe protocolo gerado.
- [ ] Permite ao usuário clicar no mapa para ajustar a coordenada.
"""
    },
    {
        "milestone": "M2: Portal Sentinela Cidadão (Área Pública)",
        "title": "Implementar Página de Consulta Pública de Protocolo com Linha do Tempo",
        "labels": ["frontend", "feature"],
        "body": """### Objetivo
Permitir ao cidadão consultar a tramitação de sua ocorrência a qualquer momento informando apenas o código do protocolo.

### Escopo
- Rota `/consulta` aceitando parâmetro `?protocolo=...`.
- Linha do tempo de status (Triagem Policial -> Validada -> Em Atendimento -> Finalizada).
- Exibição segura que não expõe dados sigilosos ou nomes de terceiros.

### Critérios de Aceitação
- [ ] Busca pelo código oficial formata e valida a entrada.
- [ ] Apresenta feedback visual claro caso o protocolo não exista (404).
- [ ] Exibe etapa atual do status com visual moderno.
"""
    },

    # Milestone 3
    {
        "milestone": "M3: Backend & Ingestão Pública",
        "title": "Endpoint de Ingestão de Ocorrência Pública do Cidadão",
        "labels": ["backend", "api", "security"],
        "body": """### Objetivo
Disponibilizar endpoint REST público para recepção segura de ocorrências registradas pela população na web.

### Escopo
- Rota `POST /v1/ocorrencias/publico`.
- Atribuição automática a um ator de sistema/agente receptor.
- Registro com status inicial `AGUARDANDO_REVISAO` na esteira padrão do domínio.
- Geração do protocolo sequencial auditável `SGOPI-AAAA-NNNNNN`.

### Critérios de Aceitação
- [ ] Responde 201 Created com dados da ocorrência e protocolo.
- [ ] Valida regras de negócio do agregado `Ocorrencia` (descrição >= 20 chars, coordenadas válidas).
- [ ] Mantém 100% de conformidade com os contratos da Arquitetura Hexagonal.
"""
    },
    {
        "milestone": "M3: Backend & Ingestão Pública",
        "title": "Endpoint de Consulta Pública de Status de Protocolo",
        "labels": ["backend", "api", "security"],
        "body": """### Objetivo
Criar endpoint REST público para consulta rápida do andamento de uma ocorrência, garantindo a privacidade dos dados.

### Escopo
- Rota `GET /v1/ocorrencias/publico/{protocolo}`.
- Retorno de dados seguros: número de protocolo, status, natureza, local e data de criação.
- Não expor CPFs, documentos ou dados de qualificação de envolvidos.

### Critérios de Aceitação
- [ ] Retorna 200 OK com resumo do status para protocolos existentes.
- [ ] Retorna 404 Not Found caso o protocolo não exista.
- [ ] Não requer token JWT.
"""
    },

    # Milestone 4
    {
        "milestone": "M4: Redesign da Área Restrita Policial",
        "title": "Redesenhar Layout com Sidebar Lateral Retrátil e User Pill",
        "labels": ["frontend", "ui/ux"],
        "body": """### Objetivo
Substituir a topbar interna simples por um AppShell profissional com menu lateral retrátil, ícones modernos e badges de status.

### Escopo
- Sidebar retrátil com links contextuais por papel (Agente, Delegado, Operador).
- Pill do usuário com nome, patente/papel e alternadores rápidos.
- Totalmente responsivo para telas menores.

### Critérios de Aceitação
- [ ] Menu colapsável com transição suave.
- [ ] Somente exibe rotas autorizadas pelo RBAC do usuário conectado.
- [ ] Integração total com o tema claro e escuro.
"""
    },
    {
        "milestone": "M4: Redesign da Área Restrita Policial",
        "title": "Redesenhar Fila de Triagem do Delegado com Distinção de Origem",
        "labels": ["frontend", "feature"],
        "body": """### Objetivo
Melhorar a experiência de triagem de ocorrências pelo Delegado, destacando ocorrências originadas pela população via web.

### Escopo
- Tabela moderna com cards expansíveis e badges de origem.
- Ações rápidas de Validar, Devolver para Correção e Rejeitar com justificativa modal.
- Filtros por antiguidade e status.

### Critérios de Aceitação
- [ ] Delegado identifica facilmente BOs de agentes vs registros de cidadãos.
- [ ] Rejeição exige justificativa mínima de 10 caracteres conforme domínio.
- [ ] Ocorrências validadas avançam para a fila de despacho do operador.
"""
    },
    {
        "milestone": "M4: Redesign da Área Restrita Policial",
        "title": "Redesenhar Painel Tático GPS e Despacho em Tempo Real",
        "labels": ["frontend", "feature", "websocket"],
        "body": """### Objetivo
Modernizar o painel tático com Leaflet, tiles adaptados ao tema e visualização clara de viaturas e ocorrências despachadas.

### Escopo
- Mapa Leaflet com alternância automática de tiles (modo escuro / modo claro).
- Marcadores com pulsos de alerta e status de telemetria GPS.
- Sugestão automática das 3 viaturas mais próximas via Haversine.

### Critérios de Aceitação
- [ ] Viaturas atualizam posição em tempo real via WebSocket sem recarregar a página.
- [ ] Painel lateral permite despacho com 1 clique.
- [ ] Latência visual abaixo de 1 segundo (RNF01).
"""
    },
    {
        "milestone": "M4: Redesign da Área Restrita Policial",
        "title": "Redesenhar Gestão de Frota e Status das Viaturas",
        "labels": ["frontend", "feature"],
        "body": """### Objetivo
Criar interface clara para controle das viaturas da corporação, disponibilidade e simulador de GPS.

### Escopo
- Grid de viaturas com status (Disponível, Em Deslocamento, Operando, Indisponível).
- Interruptor para iniciar e pausar o simulador de telemetria.
- Filtros por prefixo e situação operacional.

### Critérios de Aceitação
- [ ] Alteração de status reflete imediatamente no mapa tático.
- [ ] Simulador de GPS pode ser acionado de forma segura.
"""
    },
    {
        "milestone": "M4: Redesign da Área Restrita Policial",
        "title": "Redesenhar Tela de Login com Identidade Visual e Atalhos de Demonstração",
        "labels": ["frontend", "ui/ux"],
        "body": """### Objetivo
Criar tela de login elegante, centralizada, com a logo oficial SGOPI e botões rápidos para apresentação e testes dos papéis de Agente, Delegado e Operador.

### Escopo
- Card de login moderno com sombras suaves e logo SGOPI.
- Botões 'Demo' de 1 clique para preencher credenciais dos usuários do seed.
- Link de retorno ao portal público do cidadão.

### Critérios de Aceitação
- [ ] Autentica com sucesso e redireciona para a rota inicial do papel correto.
- [ ] Exibe mensagens de erro amigáveis para credenciais inválidas.
- [ ] Suporta tema claro e escuro com alto contraste.
"""
    },

    # Milestone 5
    {
        "milestone": "M5: Qualidade, Testes & Documentação",
        "title": "Criar Testes Automatizados E2E do Fluxo Cidadão ao Despacho",
        "labels": ["qa", "testing"],
        "body": """### Objetivo
Automatizar o fluxo ponta a ponta: registro cidadão -> triagem delegado -> despacho operador.

### Escopo
- Teste E2E cobrindo a submissão no formulário público.
- Teste de login como Delegado e aprovação da ocorrência.
- Teste de login como Operador e verificação no painel tático.

### Critérios de Aceitação
- [ ] Script roda em ambiente CI/CD ou local com sucesso.
- [ ] Relatório de teste gerado com sucesso.
"""
    },
    {
        "milestone": "M5: Qualidade, Testes & Documentação",
        "title": "Atualizar Documentação de Engenharia e Wiki com a Arquitetura Dual",
        "labels": ["documentation"],
        "body": """### Objetivo
Manter a rastreabilidade acadêmica atualizada na DOCUMENTACAO_DE_ENGENHARIA.md e na Wiki com os fluxos do portal público do cidadão.

### Escopo
- Adicionar caso de uso do registro público ao diagrama de casos de uso e matriz MoSCoW.
- Documentar os endpoints públicos `/v1/ocorrencias/publico`.
- Atualizar capturas de tela do novo design do sistema.

### Critérios de Aceitação
- [ ] Documentação reflete 100% o que está em execução no código.
- [ ] Wiki atualizada para a banca e apresentação final.
"""
    }
]


def requisicao_github(metodo, endpoint, dados=None, token=None):
    url = f"https://api.github.com/repos/{REPO}{endpoint}"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "SGOPI-Sentinela-Automation",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    corpo = json.dumps(dados).encode("utf-8") if dados else None
    req = urllib.request.Request(url, data=corpo, headers=headers, method=metodo)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detalhe = e.read().decode("utf-8")
        print(f"Erro HTTP {e.code} em {endpoint}: {detalhe}", file=sys.stderr)
        raise


def obter_ou_criar_milestone(nome, desc, token, mapa_milestones):
    if nome in mapa_milestones:
        return mapa_milestones[nome]
    try:
        res = requisicao_github("POST", "/milestones", {"title": nome, "description": desc}, token)
        num = res.get("number")
        mapa_milestones[nome] = num
        print(f"  + Milestone criada: '{nome}' (#{num})")
        return num
    except Exception as e:
        print(f"  ! Aviso ao criar milestone '{nome}': {e}")
        return None


def carregar_milestones_existentes(token):
    try:
        res = requisicao_github("GET", "/milestones?state=all", token=token)
        return {m["title"]: m["number"] for m in res}
    except Exception:
        return {}


def main():
    parser = argparse.ArgumentParser(description="Cadastra issues do SGOPI Sentinela no GitHub")
    parser.add_argument("--token", help="GitHub Personal Access Token (PAT)")
    parser.add_argument("--dry-run", action="store_true", help="Apenas exibe as issues sem cadastrar no GitHub")
    args = parser.parse_args()

    token = args.token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

    print(f"==================================================")
    print(f"   SGOPI Sentinela — Cadastro Automatizado de Issues")
    print(f"   Repositório: {REPO}")
    print(f"   Total de Issues Mapeadas: {len(ISSUES)}")
    print(f"==================================================")

    if args.dry_run or not token:
        if not token and not args.dry_run:
            print("\nNenhum token foi fornecido. Executando em modo --dry-run (apenas visualização).\n"
                  "Para cadastrar diretamente no GitHub, execute:\n"
                  "    python3 scripts/cadastrar_issues_github.py --token <SEU_PAT>\n")
        for i, issue in enumerate(ISSUES, 1):
            print(f"\n[#{i:02d}] {issue['title']}")
            print(f"      Milestone: {issue['milestone']}")
            print(f"      Labels:    {', '.join(issue['labels'])}")
            print(f"      Preview:   {issue['body'].strip().splitlines()[0]}")
        return

    print("\nConectando à API do GitHub...")
    mapa_milestones = carregar_milestones_existentes(token)

    # 1. Garantir Milestones
    print("\n1. Verificando Milestones...")
    for m in MILESTONES:
        obter_ou_criar_milestone(m["title"], m["description"], token, mapa_milestones)

    # 2. Cadastrar Issues
    print("\n2. Cadastrando Issues no repositório...")
    sucessos = 0
    for i, issue in enumerate(ISSUES, 1):
        num_milestone = mapa_milestones.get(issue["milestone"])
        payload = {
            "title": issue["title"],
            "body": issue["body"],
            "labels": issue["labels"],
        }
        if num_milestone:
            payload["milestone"] = num_milestone

        try:
            res = requisicao_github("POST", "/issues", payload, token)
            issue_url = res.get("html_url", "")
            issue_num = res.get("number", i)
            print(f"  [OK] #{issue_num} - {issue['title']} -> {issue_url}")
            sucessos += 1
        except Exception as e:
            print(f"  [FALHA] {issue['title']}: {e}")

    print(f"\nConcluído! {sucessos}/{len(ISSUES)} issues cadastradas com sucesso em {REPO}.")


if __name__ == "__main__":
    main()
