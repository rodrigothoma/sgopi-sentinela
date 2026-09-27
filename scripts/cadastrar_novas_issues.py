#!/usr/bin/env python3
"""
Script de automação para cadastro das novas issues do fechamento do MVP (Inquéritos, Laudos, Medidas Protetivas e Pin SVG)
e vinculação ao Kanban do GitHub Projects.
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

parser = argparse.ArgumentParser(description="Cadastro de novas issues e Kanban no GitHub Projects")
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

NOVAS_ISSUES = [
    {
        "milestone": "M4: Centro de Comando Tático, Despacho & Inteligência",
        "title": "Pin Interativo SVG de Localização e Despacho no Mapa (DEC-03 / RF02)",
        "labels": ["frontend", "ui/ux", "enhancement"],
        "assignees": ["fadekanaan"],
        "status": "In progress",
        "body": """### Objetivo
Implementar marcadores visuais modernos vetoriais em SVG (*Pin de Local do Fato* e *Alvo de Despacho*) com pulso de radar (*ripple pulse*) e ancoragem precisa no mapa Leaflet, substituindo marcadores padrão cinzas/azuis e permitindo seleção intuitiva de localização no registro de ocorrência e no painel de despacho.

### Contexto & Regras de Engenharia
- O sistema precisa destacar com clareza a coordenada exata selecionada pelo usuário durante o clique no mapa (DEC-03).
- Deve suportar tema claro e escuro (`--primary`, `--danger`, `--ink`).
- Utilizado tanto no formulário de registro de ocorrência (cidadão e agente) quanto no painel tático de despacho.

### Tarefas / Critérios de Aceitação
- [ ] Criar geradores de ícones vetoriais SVG `iconePinFato` e `iconeAlvoDespacho` em `leaflet.ts`.
- [ ] Integrar o pin animado com sombra e anel de pulso no componente `SeletorCoordenada.tsx`.
- [ ] Integrar o destaque do ponto de despacho da ocorrência selecionada no `MapaTatico.tsx`.
- [ ] Garantir que o arraste e o clique atualizem as coordenadas e posicionem a ponta do pin com exatidão geodésica.
"""
    },
    {
        "milestone": "M3: Módulo Operacional & Policial (Área Restrita)",
        "title": "Gestão de Inquéritos Policiais e Vinculação de Ocorrências com Sugestão de Conexões (RF06 / UC06)",
        "labels": ["backend", "frontend", "feature"],
        "assignees": ["fadekanaan"],
        "status": "In progress",
        "body": """### Objetivo
Implementar o módulo completo de Gestão de Inquéritos Policiais (IP) para o Delegado de Polícia, permitindo a instauração formal de inquéritos e o agrupamento de múltiplas ocorrências policiais validadas sob o mesmo inquérito, com motor inteligente de sugestão de conexões criminais conforme o caso de uso UC06 e diagrama de sequência sq06.

### Contexto & Regras de Engenharia
- Atende ao requisito funcional RF06 e ao caso de uso diagramado UC06 / sq06.
- Apenas ocorrências com status `VALIDADA` podem ser vinculadas a inquéritos.
- Regra de unicidade de vínculo principal: cada ocorrência vincula-se a apenas um inquérito principal ativo.
- Motor de conexões baseado em suspeitos em comum (documento/nome), proximidade geográfica (< 2.0 km) e mesma natureza/tipificação penal.
- Arquitetura Hexagonal estrita com persistência relacional auditada (RNF03 / RNF05).

### Tarefas / Critérios de Aceitação
- [ ] Criar entidade de domínio `Inquerito` e enums de status (`EM_ANDAMENTO`, `CONCLUIDO`, `ARQUIVADO`).
- [ ] Adicionar relacionamento e regras de vinculação na entidade `Ocorrencia`.
- [ ] Criar portas inbound (`InterfaceGerirInqueritos`) e outbound (`RepositorioInquerito`).
- [ ] Criar casos de uso `InstaurarInquerito`, `ListarInqueritos`, `VincularOcorrenciasInquerito` e `SugerirConexoesOcorrencias`.
- [ ] Modelar tabela `inqueritos`, foreign key `inquerito_id` em `ocorrencias` e tabela sequencial de numeração `IP-AAAA-NNNNNN`.
- [ ] Criar migration Alembic para PostgreSQL.
- [ ] Implementar rotas REST FastAPI em `/v1/inqueritos` com controle RBAC (Delegado).
- [ ] Desenvolver interface frontend (`InqueritosPage.tsx`, modal de instauração e assistente de vinculação com sugestões de conexões).
- [ ] Cobertura de testes unitários, testes de integração e testes E2E.
"""
    },
    {
        "milestone": "M3: Módulo Operacional & Policial (Área Restrita)",
        "title": "Gestão e Juntada de Laudos Periciais com Validação Digital e Integridade SHA-256 (RF07 / UC07)",
        "labels": ["backend", "frontend", "feature", "security"],
        "assignees": ["fadekanaan"],
        "status": "In progress",
        "body": """### Objetivo
Implementar o módulo de Gestão de Laudos Periciais emitidos pela Polícia Científica/Perícia Técnica, permitindo a solicitação pelo Delegado, confecção, upload do laudo oficial em PDF assinado digitalmente, validação de integridade criptográfica com hash SHA-256 e juntada aos autos da ocorrência, inquérito ou itens apreendidos (RF07 / UC07).

### Contexto & Regras de Engenharia
- Atende ao requisito funcional RF07 e ao caso de uso diagramado UC07 / sq07.
- Laudos periciais são estritamente imutáveis após a homologação (RNF03). Retificações geram aditamentos auditados sem apagar a peça original.
- Vinculação flexível: à ocorrência policial, ao inquérito policial ou a um item específico do inventário de apreensões (RF03).
- Validação criptográfica do arquivo com cálculo automático de hash SHA-256 no momento do upload.

### Tarefas / Critérios de Aceitação
- [ ] Criar entidade de domínio `LaudoPericial` com regras de integridade e tipos de perícia (Balística, Toxicológica, Local de Crime, etc.).
- [ ] Criar portas e casos de uso: `SolicitarPericia`, `AnexarLaudoPericial`, `ConsultarLaudos` e `DownloadLaudoPericial`.
- [ ] Modelar tabela `laudos_periciais` e tabela sequencial de referência `LP-AAAA-NNNNNN`.
- [ ] Criar migration Alembic para PostgreSQL.
- [ ] Implementar rotas FastAPI em `/v1/laudos` com proteção por papel (`PERITO`, `DELEGADO`).
- [ ] Desenvolver interface frontend (`LaudosPage.tsx` e aba de laudos no detalhe da ocorrência e inquérito).
- [ ] Testes unitários e de integração de upload com verificação do hash SHA-256.
"""
    },
    {
        "milestone": "M3: Módulo Operacional & Policial (Área Restrita)",
        "title": "Gestão e Monitoramento de Medidas Protetivas de Urgência e Prazos Judiciais (RF09 / UC09)",
        "labels": ["backend", "frontend", "feature"],
        "assignees": ["fadekanaan"],
        "status": "In progress",
        "body": """### Objetivo
Implementar o módulo de Medidas Protetivas de Urgência e Restrições Judiciais vinculadas a indivíduos qualificados em ocorrências policiais, permitindo o cadastramento de restrições (afastamento, proibição de contato, perímetro mínimo), controle ativo de prazos de vigência e prorrogações auditadas pelo Delegado (RF09 / UC09).

### Contexto & Regras de Engenharia
- Atende ao requisito funcional RF09 e ao caso de uso diagramado UC09 / sq09.
- Medida vincula a ocorrência de origem, a vítima protegida e o autor/agressor qualificado.
- Regra de controle temporal: prazo obrigatório não retroativo, cálculo automático da data de término e alerta visual de proximidade de vencimento.
- Prorrogação e revogação exigem fundamentação formal do Delegado de Polícia gravada na trilha de auditoria.

### Tarefas / Critérios de Aceitação
- [ ] Criar entidade de domínio `MedidaProtetiva` com cálculo de vigência, status (`ATIVA`, `RENOVADA`, `REVOGADA`, `EXPIRADA`) e tipos de restrição.
- [ ] Criar portas e casos de uso: `ConcederMedidaProtetiva`, `RenovarMedidaProtetiva`, `RevogarMedidaProtetiva` e `ListarMedidasProtetivas`.
- [ ] Modelar tabela `medidas_protetivas` e sequencial `MP-AAAA-NNNNNN`.
- [ ] Criar migration Alembic para PostgreSQL.
- [ ] Implementar endpoints FastAPI em `/v1/medidas-protetivas` restritos ao perfil `DELEGADO`.
- [ ] Desenvolver interface frontend (`MedidasProtetivasPage.tsx` com badges de dias restantes e modal de concessão e renovação).
- [ ] Testes unitários e de integração para validação de prazos e segurança RBAC.
"""
    }
]

def req_api(metodo, endpoint, payload=None):
    url = f"https://api.github.com/repos/{REPO}{endpoint}"
    dados = json.dumps(payload).encode("utf-8") if payload else None
    req = urllib.request.Request(url, data=dados, method=metodo)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "SGOPI-Automation")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def req_graphql(query, variables):
    url = "https://api.github.com/graphql"
    dados = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    req = urllib.request.Request(url, data=dados, method="POST")
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "SGOPI-Automation")
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        if "errors" in res:
            raise RuntimeError(f"Erro GraphQL: {res['errors']}")
        return res

def main():
    if not TOKEN:
        print("=" * 60)
        print("  ERRO: Nenhum GitHub Personal Access Token (PAT) informado.")
        print("  Use: python3 scripts/cadastrar_novas_issues.py --token <SEU_TOKEN>")
        print("  Ou exporte: export GITHUB_TOKEN=<SEU_TOKEN>")
        print("=" * 60)
        sys.exit(1)

    print("=" * 60)
    print("  SGOPI SENTINELA — CADASTRO DAS NOVAS ISSUES DO MVP")
    print(f"  Repositório: {REPO}")
    print(f"  Project: {PROJECT_ID}")
    print("=" * 60)

    # 1. Carregar Milestones existentes
    milestones_resp = req_api("GET", "/milestones?state=all&per_page=100")
    milestones_map = {m["title"]: m["number"] for m in milestones_resp}

    # 2. Criar cada issue e vincular ao Kanban
    sucessos = 0
    for idx, iss in enumerate(NOVAS_ISSUES, 1):
        num_milestone = milestones_map.get(iss["milestone"])
        payload = {
            "title": iss["title"],
            "body": iss["body"],
            "labels": iss["labels"],
            "assignees": iss.get("assignees", [])
        }
        if num_milestone:
            payload["milestone"] = num_milestone

        try:
            res_issue = req_api("POST", "/issues", payload)
            issue_num = res_issue["number"]
            issue_node_id = res_issue["node_id"]
            issue_url = res_issue["html_url"]
            print(f"\n[#{issue_num}] {iss['title']}")
            print(f"  Link: {issue_url}")
            print(f"  Responsáveis: {iss.get('assignees', [])}")

            # Adicionar ao Project Kanban
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

            # Mover para coluna "In progress"
            status_nome = iss.get("status", "In progress")
            status_opt_id = STATUS_OPTIONS.get(status_nome, STATUS_OPTIONS["In progress"])

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
            time.sleep(0.5)
        except Exception as e:
            print(f"  ! Erro ao cadastrar issue '{iss['title']}': {e}")

    print("\n" + "=" * 60)
    print(f"  CONCLUÍDO: {sucessos}/{len(NOVAS_ISSUES)} issues criadas e vinculadas ao Kanban em 'In progress'.")
    print(f"  Quadro: https://github.com/users/rodrigothoma/projects/2")
    print("=" * 60)

if __name__ == "__main__":
    main()
