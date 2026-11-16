# Relatório de Refatoração — SGOPI Sentinela

**Período:** 06 a 16/11/2026 · **Branch:** `fade` (integrada na `dev`) · **Responsável:** Fade Hassan Husein Kanaan

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
| Testes automatizados do backend | 844 | 1006 |
| Cobertura de testes (`domain/` + `application/`) | 95,4% | 97,0% |
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
| Operações de auditoria digitadas à mão, com grafias divergentes | **Eventos de auditoria tipados** (ver 3.5) | `79b5a8d` → `a03026f` |
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

### 3.5 Revisão após a apresentação — auditoria por eventos tipados

Na apresentação, o catálogo de auditoria (dois enums com os nomes das operações) foi apontado como fora do padrão: auditoria é a parte dinâmica do sistema, e o esperado é modelá-la com classes. A refatoração seguiu o padrão de **eventos de auditoria** (*audit events*):

| Antes | Depois |
| :--- | :--- |
| Enums `OperacaoAuditada`/`EntidadeAuditada` e 38 pontos montando `RegistroAuditoria` à mão, com o payload escrito em cada caso de uso | Classe base abstrata `EventoAuditoria` e **48 subclasses**, uma por ação (ex.: `OcorrenciaValidada`, `MedidaRevogada`), agrupadas por agregado em `domain/<agregado>/auditoria.py` |
| Mesmo payload repetido (ex.: `{status, versao}` em 4 lugares) | Classes intermediárias abstratas (`MudancaStatusOcorrencia`, `DecisaoSobreOcorrencia`, `EventoGestaoUsuario`...) concentram o que é comum |
| Catálogo mantido à mão e filtro da tela com 24 de 48 operações | Cada subclasse se registra sozinha; o catálogo e o filtro da tela (`GET /v1/auditoria/catalogo`) são gerados das classes |
| Quem/quando/IP passados em cada chamada (7 pontos sem IP) | `ContextoAuditoria`, montado por `ator.contexto_auditoria(agora)`, separado do evento |

- **Padrões:** Template Method (`para_registro` monta o registro; cada subclasse só fornece `id_entidade` e os dados), registro automático de subclasses (`__init_subclass__`, que recusa nome fora do formato `dominio.acao` ou repetido) e herança em camadas (base → agregado → ação).
- **Compatibilidade:** os nomes gravados e as chaves dos dados são os mesmos de antes — um teste compara o catálogo gerado com as 48 operações e 16 entidades já existentes, e os testes antigos de payload continuaram passando sem alteração.
- **Correções de carona:** registro sem IP em 7 pontos, alerta de vencimento auditado fora da transação, desativação/reativação de usuário gravadas como texto solto e blocos de gravação duplicados nos ramos com e sem unidade de trabalho.
- **Verificação:** 1006 testes do backend (incluindo os de ponta a ponta), cobertura de 97,0% e os 4 contratos da arquitetura hexagonal mantidos.

---

## 4. Onde ficou cada responsabilidade

Todos os novos componentes estão na camada de domínio (Python puro), conforme a arquitetura hexagonal. Caminhos relativos a `backend/src/`.

| Responsabilidade | Arquivo |
| :--- | :--- |
| Permissões (RBAC — RNF02) | `domain/usuario/permissoes.py` |
| Eventos de auditoria (RNF03): classe base e contexto | `domain/auditoria/evento.py`, `domain/auditoria/contexto.py` |
| Eventos de cada agregado | `domain/<agregado>/auditoria.py` (ex.: `domain/ocorrencia/auditoria.py`) |
| Catálogo da trilha (gerado das classes) | `domain/auditoria/catalogo_eventos.py` e `GET /v1/auditoria/catalogo` |
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
- **Auditoria como eventos, não como lista de nomes:** permissões são uma tabela estática (quem pode o quê); auditoria é o registro de algo que aconteceu, com dados diferentes em cada ação. Por isso cada ação virou uma classe que sabe montar seus próprios dados, e o catálogo passou a ser consequência das classes.
- **Trilha de auditoria preservada:** como a auditoria é *append-only*, os registros antigos não foram reescritos; as classes guardam as grafias legadas para leitura.

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
- Comparação completa no GitHub: [`2b07f82...fade`](https://github.com/rodrigothoma/sgopi-sentinela/compare/2b07f82...fade) · só a revisão da auditoria: [`db7eb68...fade`](https://github.com/rodrigothoma/sgopi-sentinela/compare/db7eb68...fade)
- Regras de arquitetura e de contribuição: [`AGENTS.md`](../AGENTS.md)
