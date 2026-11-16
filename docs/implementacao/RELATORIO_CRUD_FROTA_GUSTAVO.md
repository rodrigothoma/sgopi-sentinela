# Cadastro da frota — edição, responsável e exclusão lógica

Registro da implementação local de 16/11/2026, anterior aos commits e à publicação do PR; o histórico Git registra a integração posterior. Esta ampliação foi solicitada depois da inspeção de viatura. O relatório da inspeção original continua sendo um recorte anterior; esta entrega **cria endpoints e uma migração**, embora não acrescente dependências.

## O que mudou para quem usa

Na página **Frota**, agora é possível:

- Cadastrar prefixo, placa e um responsável opcional, como nome livre.
- Editar os três campos e remover o responsável deixando o campo vazio.
- Cancelar uma edição antes de salvar.
- Excluir um cadastro mediante confirmação. A retirada é lógica: preserva registro, UUID e vínculos históricos.
- Continuar alternando a disponibilidade pelos controles existentes.

O formulário tem rótulos, limites de tamanho, modo de edição identificado e botões bloqueados durante o envio. A tabela mostra o responsável ou **Sem responsável**. A tabela possui rolagem horizontal quando necessário, e as ações podem quebrar linha.

No **Painel Tático**, selecionar uma viatura pela frota ou pelo mapa mostra também seu responsável no card. Se outra tela editar esse cadastro, o painel recebe o evento, recarrega a lista e atualiza o card aberto. Ao excluir a unidade, o painel retira a unidade da lista e fecha a inspeção correspondente. Edição de prefixo/placa atualiza também tooltip e título do marcador.

## Regras e decisões

| Decisão | Motivo e comportamento |
| --- | --- |
| Nome livre, opcional | Escolha expressa do usuário. Não há vínculo com conta, usuário ou autorização do SGOPI. Limite de 120 caracteres; espaços nas bordas são removidos; vazio vira `null`. |
| Identificação única | Prefixo e placa continuam únicos. A edição pode conservar a identificação do próprio registro; não pode usar a de outra viatura. Identificações excluídas continuam reservadas, pois o registro histórico permanece. |
| Exclusão lógica | `ativo = false` e situação `INDISPONIVEL`; nenhum `DELETE` é executado na tabela de viaturas. Listagens operacionais e indicadores ignoram os excluídos; consultas internas por identidade preservam o acesso histórico. |
| Bloqueio durante atendimento | A exclusão é recusada em `EM_DESLOCAMENTO`/`OPERANDO` e quando existe ordem ativa. O backend aplica a regra mesmo se uma chamada contornar o botão desabilitado. |
| Edição preserva operação | Alterar nome/prefixo/placa não modifica posição GPS, situação ou UUID. A edição é permitida durante atendimento; a exclusão, não. |
| Concorrência | Edição e exclusão enviam a versão vista na tela. Se mudou, o backend responde 409. A persistência mantém a verificação otimista existente. O formulário permanece preenchido em caso de erro. |
| Auditoria | Novas operações `viatura.editar` e `viatura.excluir`, com ator, instante e dados antes/depois, na transação da alteração. Cadastro passa a auditar também o responsável. |
| Eventos após commit | `ViaturaCadastroAlterado` e `ViaturaExcluida` carregam apenas o identificador. Os consumidores recarregam os detalhes pela API autorizada. Não foi criado outro WebSocket. |

Excluir não oferece uma operação de restaurar nesta interface. Não há promessa de exclusão definitiva ou anonimização do responsável. O campo é um dado descritivo, não uma confirmação de quem está efetivamente dentro da viatura.

## Como o código foi organizado e como explicar

### 1. Entidade de domínio

Arquivo: `backend/src/domain/viatura/entity.py`.

`Viatura` ganhou `responsavel` e `ativo`. A normalização existente de prefixo/placa foi preservada. As constantes `LIMITE_PREFIXO`, `LIMITE_PLACA` e `LIMITE_RESPONSAVEL` centralizam os limites usados também na borda HTTP.

`alterar_cadastro` valida os novos campos e chama `_tocar`, o mecanismo de versão já existente. `excluir` aplica a proteção de situação, marca a exclusão lógica e incrementa a versão. `despachavel` exige também cadastro ativo.

**Fala possível:** “Coloquei as regras da viatura no domínio, sem importar banco ou FastAPI. Editar identificação não deve alterar o GPS ou o atendimento.”

### 2. Casos de uso e portas

Arquivos: `application/ports/inbound/interface_gerir_viaturas.py` e `application/use_cases/viatura/manter_cadastro.py`, sob `backend/src/`.

Há um caso de uso `EditarViatura` e outro `ExcluirViatura`, cada um com um `executar`. As entradas possuem versão. As funções auxiliares `exigir_versao`, `exigir_identificacao_unica` e `dados_cadastro` deixam explícitas as verificações e o snapshot auditável.

**SRP:** edição e exclusão têm responsabilidades distintas. A verificação de uma ordem ativa pertence à orquestração da exclusão e utiliza a porta de ordens existente.

**DIP:** os casos recebem portas de repositório, relógio, auditoria, unidade de trabalho e publicação; não instanciam SQLAlchemy. A composição concreta fica em `infrastructure/di.py`, conforme a arquitetura existente.

**Fala possível:** “Cada caso de uso coordena uma ação. Ele pede persistência por uma interface; não precisa saber se o armazenamento é PostgreSQL ou o fake do teste.”

Isso usa e amplia a arquitetura já presente; não significa que a arquitetura hexagonal ou o controle de versão tenham sido criados nesta entrega.

### 3. Persistência e API

A migração `0018_cadastro_viatura.py` acrescenta duas colunas sem apagar registros. Cadastros anteriores ficam ativos, sem responsável. O Data Mapper existente foi ampliado para transportar esses campos entre domínio e ORM.

Rotas novas:

- `PATCH /v1/viaturas/{id}` com `prefixo`, `placa`, `responsavel` e `versao`.
- `DELETE /v1/viaturas/{id}?versao=N`, retornando 204 após exclusão lógica. O verbo HTTP não implica DELETE SQL.

Cadastro e listagem existentes passam a aceitar/devolver o responsável. Os atos de gestão continuam exigindo `GERIR_FROTA`. `carregar_viatura` recusa cadastro excluído para operações atuais. A listagem SQL e o fake compartilham o filtro de ativos; há teste de contrato para ambos. A consulta de indicadores recebeu o mesmo filtro para não contar um cadastro retirado da frota.

**Data Mapper:** padrão existente, adaptado aos campos novos. Não foi criada uma segunda camada de conversão paralela.

### 4. Interface e tempo real

Arquivos: `FrotaPage.tsx`, `viaturasService.ts`, `PainelTaticoPage.tsx`, `InspecaoViatura.tsx` e `MapaTatico.tsx`, em `frontend/src/`.

A página Frota coordena formulário e ações. O serviço concentra HTTP. A confirmação reutiliza `useConfirmacao`, que já existia, com foco inicial em Cancelar. `ocupado` bloqueia ações durante requisições. Os textos novos estão em português e inglês.

O painel continua usando `useTempoReal`; a Frota usa `useTempoRealListener`. Ambos reutilizam o canal Observer **já existente**. O card não se inscreve: recebe a viatura por props. O painel guarda o ID selecionado e deriva os dados da lista atual, evitando duplicação do cadastro no estado do card.

**Fala possível:** “Salvar o responsável dispara um aviso pelo canal existente. O painel recarrega a frota e passa a viatura atualizada ao card. O card continua responsável apenas pela apresentação.”

Não foram introduzidos Repository, Observer, Unit of Work ou Data Mapper do zero. Foram usados os contratos e padrões do projeto. Não foi medido ganho de desempenho nem alegada aplicação de todos os princípios SOLID.

## Validação manual sugerida

**Estes passos são um roteiro para o usuário. Os comportamentos citados possuem testes automatizados, mas o usuário ainda não informou validação manual desta ampliação.** A validação manual anterior limitou-se aos passos 4.2–4.5 do relatório da inspeção original.

O backend local já recebeu a migração 0018. Para outro ambiente, com o banco correto configurado, executar `cd backend && uv run alembic upgrade head`. Não executar `npm run e2e:db` no banco de desenvolvimento, pois esse comando reinicia o esquema.

1. **Criar sem responsável.** Entrar como operador e abrir Frota. Cadastrar `DEMO-CRUD` e uma placa ainda não usada. Deixar responsável vazio. A linha deve exibir **Sem responsável**, sem afetar as outras viaturas.
2. **Editar identificação e nome.** Clicar em Editar nessa linha, alterar prefixo/placa e informar `Ana Exemplo`. Salvar. A tabela deve refletir os três campos. Recarregar a página para conferir persistência.
3. **Inspecionar no Painel Tático.** Abrir o painel e clicar no prefixo da mesma unidade. O card deve mostrar `Ana Exemplo`. Uma viatura recém-criada pode estar sem posição: a seleção pela frota funciona e Centralizar fica desabilitado com explicação.
4. **Conferir atualização com card aberto.** Manter a unidade selecionada no painel e abrir Frota em outra aba autenticada. Editar o responsável para `Bruno Exemplo`. O card deve atualizar sem recarregar a página. Se remover o nome e salvar, deve mostrar **Sem responsável**. Com posição disponível, conferir também prefixo/placa no tooltip após edição.
5. **Cancelar.** Entrar na edição, alterar um campo e clicar em Cancelar edição. A tabela deve manter os dados salvos. Reabrir Editar deve carregar os dados persistidos, não o rascunho cancelado.
6. **Recusar duplicidade.** Tentar salvar prefixo ou placa de outra viatura. Esperar erro, com o formulário preservado. Corrigir ou cancelar o rascunho. Cadastros excluídos também mantêm sua identificação reservada.
7. **Conferir versão obsoleta.** Abrir Editar da mesma viatura em duas abas. Salvar uma alteração na primeira. Tentar salvar o formulário que já estava aberto na segunda: deve retornar conflito e não sobrescrever a primeira. A lista pode atualizar por evento; o rascunho continua com sua versão original. Cancelar e reabrir Editar para trabalhar sobre a versão atual.
8. **Cancelar exclusão.** Clicar em Excluir na unidade de demonstração. O diálogo deve iniciar em Cancelar. Cancelar: a unidade continua disponível.
9. **Excluir de fato.** Manter o card da unidade aberto em outra aba. Confirmar Excluir na Frota. A linha sai da frota ativa; o card deve fechar no painel. O registro é preservado no banco. Não excluir uma unidade real apenas para demonstrar: usar o cadastro de demonstração criado no passo 1.
10. **Atendimento em andamento.** Se houver uma unidade em `EM_DESLOCAMENTO` ou `OPERANDO`, Excluir fica desabilitado. O bloqueio no backend e a ordem ativa são verificados por testes; não interromper um atendimento real para demonstrar.

## Testes e evidências

Testes novos desta ampliação:

- Sete casos de domínio: responsável, normalização/remoção, exclusão e situações bloqueadas, limites de tamanho.
- Quatro testes de casos de uso: auditoria/eventos, preservação histórica, ordem ativa e permissão.
- Três testes HTTP/integração: CRUD com versão, duplicidade/permissões e indicadores.
- Dois casos de contrato, a mesma regra de exclusão contra fake e SQLAlchemy.
- Dois Vitest de apresentação: responsável informado e ausência de responsável.
- Quatro cenários Cypress de CRUD: cadastro/edição/remoção de nome; cancelamento/confirmação; conflito/bloqueio; eventos atualizando o card, identificação no marcador e fechamento após exclusão.

Os testes do card falharam antes por não existir a informação de responsável. Os novos testes de domínio/HTTP inicialmente falharam pela ausência dos comportamentos. O teste dos indicadores reproduziu a contagem da viatura excluída. O Cypress reproduziu o tooltip com identificação antiga antes da correção.

Os quatro Cypress do CRUD e os cinco da inspeção passaram. Usam REST, WS e tiles controlados; não provam, isoladamente, o transporte real da edição via PostgreSQL até o navegador. O backend tem testes próprios de HTTP e persistência. A API local real foi consultada após a migração: os cinco cadastros existentes retornam os campos novos.

A migração foi executada no PostgreSQL local e `alembic check` não apontou diferenças. A verificação completa usa SQLite isolado e inclui arquitetura, lint, migrações, testes/cobertura, TypeScript, Vitest, build e audit. O resultado final da execução está registrado ao fim deste documento.

**Pendência anterior preservada:** a spec `notificacoes-tempo-real.cy.ts` falhou na inspeção anterior e foi comparada com a base commitada. A causa conclusiva permanece pendente; esta ampliação não declara essa spec corrigida nem a suíte inteira do Cypress aprovada.

Logs locais temporários: `/tmp/sgopi-crud-verificar-final.log`, `/tmp/sgopi-crud-cypress-final.log` e `/tmp/sgopi-crud-cypress-title.log`.

## Dez ocorrências prontas para demonstração

Foram criadas pela API policial real, com usuário agente do seed e conteúdo explicitamente fictício. Nenhuma foi validada ou despachada. Uma conferência posterior confirmou as dez em `AGUARDANDO_REVISAO`.

| Protocolo | Natureza |
| --- | --- |
| SGOPI-2026-000018 | Furto |
| SGOPI-2026-000019 | Dano |
| SGOPI-2026-000020 | Roubo |
| SGOPI-2026-000021 | Ameaça |
| SGOPI-2026-000022 | Perturbação do sossego |
| SGOPI-2026-000023 | Estelionato |
| SGOPI-2026-000024 | Receptação |
| SGOPI-2026-000025 | Furto de veículo |
| SGOPI-2026-000026 | Lesão corporal |
| SGOPI-2026-000027 | Vandalismo |

Entrar como delegado → Fila de revisão → Aguardando revisão. Se houver filtro preenchido, limpar ou buscar pelo protocolo. Escolher uma ocorrência para demonstrar validar/devolver/rejeitar; somente uma validada segue para despacho pelo operador. Não há necessidade de recriar ou reiniciar o banco.


## Resultado final executado

| Verificação | Resultado em 16/11/2026 |
| --- | --- |
| `./scripts/verificar.sh` | Aprovado, todas as etapas verdes |
| Arquitetura hexagonal / Ruff | Aprovados, sem violações / erros |
| Migração SQLite isolada + `alembic check` | Aprovados |
| Backend completo, incluindo E2E da API | 980 testes passando; cobertura total 96,82%; pisos por arquivo aprovados |
| TypeScript / Vitest | Sem erros; 44 testes passando em 11 arquivos |
| Build / auditoria de dependências de produção | Aprovado; 0 vulnerabilidades reportadas |
| Cypress de CRUD | 4/4 passando, incluindo título e tooltip após edição |
| Cypress de inspeção | 5/5 passando |
| PostgreSQL local | Migração 0018 aplicada; `alembic check` sem diferenças |
| `git diff --check` | Sem erros |

Os totais de backend e Vitest incluem a suíte herdada; não são apresentados como testes todos criados nesta entrega. Os novos testes estão discriminados na seção anterior. “Tudo verde” refere-se às etapas de `verificar.sh` e às duas specs selecionadas, não à suíte completa do Cypress nem à pendência anterior de notificações.

**Validação do usuário:** os cenários novos de CRUD/responsável estão cobertos por testes automatizados, não validados manualmente pelo usuário até este registro. Houve ainda conferência da API local e aplicação da migração pelo agente; isso não substitui sua revisão visual e funcional.
