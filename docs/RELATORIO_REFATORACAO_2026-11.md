# Relatório de Refatoração — SGOPI Sentinela

**Período:** 06 a 09/11/2026 · **Branch:** `fade` (integrada na `dev`) · **Responsável:** Fade Hassan Husein Kanaan

Este relatório resume o que foi corrigido e refatorado no sistema, em ordem de prioridade, e o que ficou planejado para as próximas etapas. O detalhamento item a item, com o commit de cada um, está no [plano de refatoração](implementacao/PLANO_REFATORACAO_2026-11.md).

---

## 1. Objetivo

1. Sincronizar a branch de trabalho com a `dev` e alinhar a documentação ao código implementado.
2. Analisar o projeto inteiro (backend, frontend e documentação) para identificar código a refatorar, duplicações e falhas.
3. Executar a primeira parte da refatoração: correção de bugs (Onda 0) e fundações do domínio (Onda 1), sem alterar a arquitetura hexagonal definida na [documentação de engenharia](DOCUMENTACAO_DE_ENGENHARIA.md).

## 2. Resultados em números

| Indicador | Antes | Depois |
| :--- | :---: | :---: |
| Falhas de segurança e de corretude corrigidas | — | 10 |
| Checagens de papel escritas à mão nos casos de uso | 15 | 0 |
| Listas de papéis duplicadas entre camadas | 20+ | 0 |
| Textos soltos na trilha de auditoria | 39 | 0 |
| Controles de versão escritos à mão (`versao += 1`) | 12 | 0 |
| Validações de texto repetidas nas entidades | 28 | 0 |
| Testes automatizados do backend | 844 | 939 |
| Cobertura de testes (`domain/` + `application/`) | 95,4% | 96,7% |
| Contratos da arquitetura hexagonal (import-linter) | 4 mantidos | 4 mantidos |
| Pipeline de CI no GitHub Actions | falhando | verde nos 3 jobs |

---

## 3. O que foi feito, por prioridade

### 3.1 Prioridade crítica — segurança e controle de acesso

| Problema encontrado | Correção | Commit |
| :--- | :--- | :---: |
| Ofícios interagências `RESERVADO` e `CONFIDENCIAL` podiam ser lidos por qualquer usuário autenticado | Regra de sigilo por papel no domínio, aplicada na consulta e na resposta a ofícios | `afe0f61` |
| O assunto de ofícios restritos vazava por notificações (enviadas a todos) e por eventos de tempo real (WebSocket) | Notificação apenas aos papéis autorizados; o evento leva o nível de sigilo e é filtrado na entrega | `2cd61e6` |
| A opção "Restrito" da tela enviava um valor inexistente no backend, e o ofício era gravado como público | Valor corrigido para `RESERVADO`; valor de sigilo desconhecido passou a ser recusado (HTTP 422) | `8bc04d6`, `8b281d1` |
| Permissões de consulta de inquéritos diferentes no frontend, no router e no caso de uso | Regra única: Delegado, Supervisor e Operador Central | `a93a08b` |

### 3.2 Prioridade alta — corretude dos dados e confiabilidade

| Problema encontrado | Correção | Commit |
| :--- | :--- | :---: |
| Medidas protetivas usavam a data em UTC: entre 21h e 24h o sistema considerava o dia seguinte | Data de calendário no fuso da operação (`America/Sao_Paulo`) | `fe5dccc` |
| A listagem de ofícios aplicava o filtro de departamento depois do limite da consulta e perdia registros | Filtros movidos para o SQL | `afe0f61` |
| Duas requisições simultâneas no primeiro ofício do ano geravam erro de numeração | Geração atômica (UPSERT), igual aos demais geradores de número | `17eda28` |
| Entidades de domínio liam o relógio do sistema e uma falha era engolida sem registro | Instante sempre vindo da porta `Relogio`; falha registrada em log | `bd3d83a` |
| Repositórios falsos dos testes não se comportavam como o banco real (versão otimista) | Fakes alinhadas ao SQL e testes de contrato que rodam a mesma bateria nos dois | `302eccf` |
| CI reprovado por vulnerabilidade de severidade alta numa dependência do frontend | Dependência atualizada (`follow-redirects` 1.16.2) | `e96de24` |

### 3.3 Prioridade média — arquitetura, duplicação e manutenibilidade

| Antes | Depois | Commit |
| :--- | :--- | :---: |
| Regras de acesso espalhadas em `if`s e tuplas de papéis copiadas entre router, caso de uso e WebSocket | **Catálogo de permissões** único (ação → papéis), consultado pelas três camadas | `2f254c1` |
| Operações de auditoria digitadas à mão, com grafias divergentes | **Catálogo de auditoria** (`OperacaoAuditada`, `EntidadeAuditada`), mantendo a leitura dos registros antigos | `79b5a8d` |
| Transições de estado escritas como `if status not in (...)` em cada método | **Máquina de estados genérica**: cada agregado declara sua tabela de transições | `de2b4fe` |
| Incremento de versão e data de atualização repetidos em cada mutação, com inconsistências | **Mixin `Versionado`** com `_tocar(instante)` nas 5 entidades versionadas | `de2b4fe` |
| Regras de negócio copiadas nos casos de uso (vínculo a inquérito, despacho, alerta de vencimento) | Regras movidas para as entidades (`exigir_vinculavel`, `exigir_despachavel`, `precisa_alerta`) | `de2b4fe`, `904d547` |
| Validações de texto e conversões de enum repetidas, números mágicos | Funções `exigir_texto` e `interpretar_enum`, constantes nomeadas | `8b281d1` |
| Enums de prioridade duplicados, cálculo de distância reimplementado, strings soltas | Escala única de prioridade, Haversine reaproveitado, enums `SinalViatura` e `TipoRestricao` | `b97f3aa` |
| Cálculo do hash do documento oficial embutido na entidade `Ocorrencia` | Estratégia de canonicalização por versão em módulo próprio | `e7daa55` |

### 3.4 Prioridade baixa — documentação e processo de desenvolvimento

| Entrega | Commit |
| :--- | :---: |
| Documentação alinhada ao código: 23 tabelas, RF10 como extra, UC06 com o motor de conexões, UC10 com a regra de sigilo | `2b07f82`, `26da69e` |
| Plano de refatoração versionado, com o progresso por item | `afd07a0`, `051790d` |
| Verificação automática antes do commit (pre-commit) e script que reproduz o CI localmente | `39b79ec`, `281c047` |
| Roteiros para agentes de IA (TDD no backend e no frontend, verificação e passagem de contexto), referenciados no `AGENTS.md` | `bd670f1` |

---

## 4. Onde ficou cada responsabilidade

Todos os novos componentes estão na camada de domínio (Python puro), conforme a arquitetura hexagonal. Caminhos relativos a `backend/src/`.

| Responsabilidade | Arquivo |
| :--- | :--- |
| Permissões (RBAC — RNF02) | `domain/usuario/permissoes.py` |
| Catálogo da trilha de auditoria (RNF03) | `domain/auditoria/catalogo.py` |
| Máquina de estados genérica | `domain/shared/maquina_estados.py` |
| Controle otimista de versão (mixin) | `domain/shared/versionado.py` |
| Validação de texto e conversão de enums | `domain/shared/validacao.py`, `domain/shared/enums.py` |
| Escala de prioridade | `domain/shared/prioridade.py` |
| Regra de sigilo de ofícios (RF10) | `domain/interagencias/entity.py` |
| Hash do documento oficial (RF08) | `domain/ocorrencia/hash_narrativa.py` |

## 5. Decisões de projeto

- **Mixin em vez de classe base com campos:** em `dataclasses`, herdar campos com valor padrão força a reordenação dos campos de todas as entidades filhas. O mixin `Versionado` traz só o comportamento, e cada entidade continua declarando seus campos.
- **Permissões organizadas por ação, não por papel:** o código sempre pergunta "este usuário pode executar esta ação?". Com a tabela por ação, mudar quem pode fazer algo é alterar uma linha, e router, caso de uso e WebSocket passam a obedecer juntos.
- **Sigilo por papel:** os usuários não têm departamento cadastrado; a credencial compatível do UC10 passou a ser o papel (tabela na seção UC10 da documentação de engenharia).
- **Trilha de auditoria preservada:** como a auditoria é *append-only*, os registros antigos não foram reescritos; o catálogo guarda as grafias legadas para leitura.

## 6. Garantia de qualidade

- Cada correção de bug foi feita com um teste que **falha no código antigo** e passa no novo (teste de regressão).
- A arquitetura foi validada pelo `import-linter` (4 contratos mantidos, nenhuma violação).
- O pipeline do GitHub Actions passou nos 3 jobs: backend com testes de ponta a ponta contra a API real, migrações no PostgreSQL 16 e frontend (tipagem, testes, build e auditoria de dependências).

## 7. Mudanças de comportamento

- Operador, Escrivão, Agente e Perito deixaram de ver ofícios confidenciais; Agente e Perito também não veem os reservados.
- Nível de sigilo, prioridade ou tipo de restrição inválidos são recusados (HTTP 422), em vez de assumirem um valor padrão.
- Cinco operações de auditoria passaram ao formato `dominio.acao` nos registros novos (ex.: `interagencias.enviar`).

---

## 8. Próximos passos, por prioridade

| Prioridade | Item | Etapa |
| :--- | :--- | :---: |
| Alta | Traduzir as 36 mensagens de erro sem tradução (inquérito, laudo e medida), hoje exibidas como chave técnica | Onda 5 |
| Alta | Mover o motor de conexões para o domínio, com parâmetros agrupados e revisão das famílias criminais | Onda 2 |
| Alta | Classe base abstrata para os casos de uso (Template Method), eliminando o fluxo repetido de carregar → aplicar → salvar → auditar | Onda 2 |
| Alta | Dividir o `di.py` (1164 linhas) em módulos por domínio | Onda 3 |
| Média | Repositório base versionado e mappers para os 8 repositórios restantes | Onda 3 |
| Média | Parâmetros nomeados no cálculo de áreas de risco e fatores únicos (metros por km, tamanho do hash) | Onda 2 |
| Média | Frontend: conexão de tempo real única, componentes comuns e divisão das páginas grandes (até 1362 linhas) | Onda 4 |
| Média | Testes unitários dos casos de uso ainda cobertos só por testes HTTP | Onda 5 |
| Baixa | Sincronizar a wiki, atualizar diagramas e documentar UC12 a UC14 | Onda 5 |
| Baixa | Testes de interface (Cypress) para inquéritos, laudos, medidas e interagências | Onda 4 |

## 9. Referências

- Plano detalhado, com o commit de cada item: [`docs/implementacao/PLANO_REFATORACAO_2026-11.md`](implementacao/PLANO_REFATORACAO_2026-11.md)
- Comparação completa no GitHub: [`2b07f82...281c047`](https://github.com/rodrigothoma/sgopi-sentinela/compare/2b07f82...281c047)
- Regras de arquitetura e de contribuição: [`AGENTS.md`](../AGENTS.md)
