# Separação lista/detalhe e responsividade do portal cidadão — implementação e validação

## 1. O que foi entregue

As páginas `/fila` e `/minhas` deixaram de mostrar lista e detalhe na mesma tela. Cada fluxo agora tem uma rota própria para o detalhe:

| Fluxo | Lista | Detalhe |
| --- | --- | --- |
| Delegado / supervisor | `/fila` | `/fila/:ocorrenciaId` |
| Agente | `/minhas` | `/minhas/:ocorrenciaId` |

O detalhe ocupa a página inteira no desktop e no mobile. A volta preserva filtros de busca e, na fila, também a aba selecionada. Links antigos no formato `?ocorrencia=<id>` continuam funcionando: são redirecionados para a rota canônica do detalhe.

As rotas públicas `/`, `/registrar-cidadao`, `/consulta` e `/autenticar` também foram ajustadas para telas de 390 px. A navegação, o hero, os cards, os formulários e o mapa passaram a se adaptar sem rolagem horizontal, preservando o layout desktop.

Não houve mudança em backend, mobile, regras de negócio, permissões ou contratos da API. Não foram criadas dependências nem migrações.

### Antes e depois, de forma resumida

| Antes | Depois |
| --- | --- |
| A lista e o detalhe dividiam a largura da tela em duas colunas. | A lista fica sozinha; o detalhe abre em uma rota própria e ocupa toda a largura útil. |
| No mobile, as duas colunas apenas empilhadas; abrir um item ainda misturava navegação e leitura. | No mobile, clicar leva a uma página de detalhe limpa, com botão de voltar no topo. |
| Um link direto precisava ajustar a aba da lista para que a ocorrência aberta ficasse visível. | O detalhe calcula a aba correta pelo status e a leva de volta na query string. |
| Filtros, aba, estado do detalhe, decisões e correção conviviam no mesmo componente. | Lista e detalhe têm estados e responsabilidades separados. |
| Notificações antigas apontavam para `/fila?ocorrencia=<id>` ou `/minhas?ocorrencia=<id>`. | Esses links são redirecionados; nenhuma notificação antiga deixa de funcionar. |

## 2. Arquivo por arquivo

### Arquivos criados

| Arquivo | Antes | Depois |
| --- | --- | --- |
| `frontend/src/utils/ocorrenciaDeepLink.ts` | Não existia. Cada página manipulava `?ocorrencia=` e a aba da fila diretamente. | Concentra as regras puras de navegação: `urlDoDetalhe`, `urlDaLista`, `lerAba`, `idOcorrenciaLegada`, `abaDoStatus` e os grupos de status da fila. Não importa React nem serviço. |
| `frontend/src/utils/__tests__/ocorrenciaDeepLink.test.ts` | Não existia. | Testa ida e volta, preservação de filtros, remoção do parâmetro legado, validação da aba, cálculo da aba pelo status e leitura do link antigo. |
| `frontend/src/pages/FilaDelegadoDetalhePage.tsx` | Não existia; esse conteúdo vivia na metade direita de `FilaDelegadoPage.tsx`. | Carrega a ocorrência pelo `:ocorrenciaId`, mantém os painéis de detalhe, prioridade, decisão e arquivamento/exclusão, e calcula o retorno para a aba correta. |
| `frontend/src/pages/MinhasOcorrenciasDetalhePage.tsx` | Não existia; esse conteúdo vivia na metade direita de `MinhasOcorrenciasPage.tsx`. | Carrega a ocorrência pelo `:ocorrenciaId`, mostra o detalhe e mantém edição, salvamento e reenvio na mesma rota. |
| `frontend/cypress/e2e/separacao-lista-detalhe.cy.ts` | Não existia. | Cobre abertura em rota própria, volta com filtros, redirecionamento do link legado e detalhe em largura integral a 390 px, com textos longos e asserções de ausência de corte nas rotas `/fila/:id` e `/minhas/:id`. |
| `frontend/cypress/e2e/portal-cidadao-mobile.cy.ts` | Não existia. | Cobre as quatro rotas públicas a 390 px: ausência de rolagem horizontal, navegação empilhada, campos e textos longos legíveis e título animado com tamanho reduzido. |

### Arquivos modificados

| Arquivo | Antes | Depois |
| --- | --- | --- |
| `frontend/src/App.tsx` | Só existiam `/fila` e `/minhas`, cada uma com lista e detalhe juntos. | Registra lazy routes `/fila/:ocorrenciaId` e `/minhas/:ocorrenciaId` com os mesmos papéis das rotas de lista. |
| `frontend/src/pages/FilaDelegadoPage.tsx` | Guardava `detalhe`, justificativa, motivo, confirmação, ações de decisão e o painel de prioridade; abria o detalhe no estado local. | Fica responsável só pela listagem, filtros, abas, badge “nova”, exportação e navegação para o detalhe. A aba passa a ser refletida em `?aba=` e links legados são redirecionados. |
| `frontend/src/pages/MinhasOcorrenciasPage.tsx` | Guardava `detalhe`, `editando` e todo o formulário de correção; abria o detalhe no estado local. | Fica responsável só pela listagem, filtros e navegação para o detalhe. Links legados são redirecionados. |
| `frontend/src/components/layout/BuscaGlobal.tsx` | Navegava para `${destino}?ocorrencia=<id>`. | Navega direto para `${destino}/<id>`. O comentário foi atualizado para descrever a rota nova. |
| `frontend/src/pages/InicioPage.tsx` | Gerava `/minhas?ocorrencia=<id>` e `/fila?ocorrencia=<id>` nos atalhos de últimas ocorrências. | Gera `/minhas/<id>` e `/fila/<id>`. |
| `frontend/src/locales/pt/ocorrencias.json` | Não havia rótulos para voltar do detalhe. | Adiciona `minhas.voltar` (“Voltar às ocorrências”) e `fila.voltar` (“Voltar à fila”). |
| `frontend/src/locales/en/ocorrencias.json` | Não havia rótulos para voltar do detalhe. | Adiciona as versões em inglês: “Back to occurrences” e “Back to queue”. |
| `frontend/src/styles.css` | `.duas-colunas` organizava lista e detalhe; em telas estreitas virava uma coluna, mas ainda na mesma página. O portal usava larguras e alturas fixas em estilos inline. | Mantém a classe existente para outros usos e acrescenta `.detalhe-pagina`/`.voltar` para limitar a largura e separar o botão de retorno do conteúdo. Empilha o `dl.grid2` do detalhe e permite quebra de badges e textos longos em telas até 640 px. Acrescenta regras escopadas ao portal para navegação, hero, cards, formulários e mapa em 390 px. |
| `frontend/src/pages/AutenticarDocumentoPage.tsx` | Usava estilos inline de largura e espaçamento próprios. | Passa a usar `.pagina.pagina-publico`, `.card.card-publico` e `.publico-acoes`, mantendo o conteúdo legível no mobile. |
| `frontend/src/pages/ConsultaProtocoloPage.tsx` | Usava estilos inline de largura e espaçamento próprios. | Passa a usar `.consulta-form` e classes públicas compartilhadas, com rótulos e valores empilhados no mobile. |
| `frontend/src/pages/RegistroCidadaoPage.tsx` | Usava estilos inline de largura e espaçamento próprios. | Passa a usar as classes públicas compartilhadas, reduzindo o mapa apenas no formulário público. |
| `frontend/src/pages/LandingPage.tsx` | O título animado recebia `fontSize={52}` fixo. | Passa a usar `var(--hero-title-font-size, 52px)`, permitindo reduzir para 26 px somente no portal mobile. |
| `frontend/src/components/painel/SeletorCoordenada.tsx` | Definia `height: 300` diretamente no componente. | Remove a altura inline; o CSS mantém 300 px no desktop e reduz para 220 px no formulário público. |
| `frontend/cypress/e2e/validacao-despacho.cy.ts` | Clicava no item e esperava `.detalhe` na mesma página; depois voltava a usar a lista sem trocar de rota. | `abrirNaFila` confere a URL da rota de detalhe; testes que voltam à lista clicam em “Voltar à fila”. Fluxo de agente confirma `/minhas/<id>`. |
| `frontend/cypress/e2e/notificacoes-tempo-real.cy.ts` | Comentário citava o link antigo; após abrir o detalhe, verificava o badge na lista ainda montada. | Comentário passa a citar o redirecionamento; a checagem do badge ocorre depois de voltar à lista. URL esperada passa a ser `/fila/`. |

## 3. Como a implementação funciona

### 3.1 Rotas e responsabilidades

`App.tsx` continua usando `RequireRole` com os mesmos papéis de antes. Mudou apenas o componente associado a cada caminho. A lista não conhece o formulário de decisão; o detalhe não conhece a consulta paginada da lista. Cada página carrega somente o serviço de que precisa.

### 3.2 Regras de URL em um único lugar

`ocorrenciaDeepLink.ts` responde três perguntas:

1. Para onde vai o clique em um item? `urlDoDetalhe`.
2. Para onde volta o botão “Voltar”? `urlDaLista`.
3. O parâmetro `?ocorrencia=` é um link legado? `idOcorrenciaLegada`.

As funções recebem `URLSearchParams` e devolvem strings. Isso permite testá-las sem navegador, seguindo a orientação da skill `frontend-tdd` de manter a regra testável fora do componente.

A url do detalhe preserva filtros e `aba`, mas remove `ocorrencia`. A volta preserva filtros, substitui `aba` pela aba calculada a partir do status e também remove `ocorrencia`.

### 3.3 Deep link legado

Notificações já existentes e links antigos ainda usam `?ocorrencia=<id>`. Ao detectar esse parâmetro, a página de lista renderiza um `<Navigate>` para a rota canônica. Isso evita alterar backend, banco ou notificações já enviadas.

Exemplo: `/minhas?protocolo=SGOPI-1&ocorrencia=abc` vira `/minhas/abc?protocolo=SGOPI-1`.

### 3.4 Volta com contexto

Na fila, o status da ocorrência define a aba de retorno:

- `AGUARDANDO_REVISAO` → aba 0;
- `EM_CORRECAO` → aba 1;
- `VALIDADA` / `EM_ATENDIMENTO` → aba 2;
- `REJEITADA` / `ENCERRADA` → aba 3;
- `ARQUIVADA` / `EXCLUIDA` → aba 4.

Isso substitui o ajuste antigo feito no estado da lista quando se abria um link direto. Se o detalhe ainda não carregou, a página usa a aba válida presente na URL.

### 3.5 Correção sem perder o contexto

Em `/minhas/:ocorrenciaId`, o estado `editando` continua controlando a alternância entre detalhe e formulário. Salvar ou reenviar atualiza o detalhe exibido e mantém o usuário na mesma rota. A correção não volta para a lista sozinha.

### 3.6 Preservação do comportamento existente

Continuam intactos:

- papéis e `RequireRole`;
- validar, devolver, rejeitar, arquivar, excluir e priorizar;
- obrigatoriedade de justificativa e confirmação de rejeição;
- correção e reenvio do agente;
- filtros em query string, exportação CSV e atualização por WebSocket;
- aba de apreensões, comprovante e autenticidade;
- geração de notificações pelo backend.

### 3.7 Ajuste de layout no detalhe mobile

O resumo da ocorrência usa `dl.grid2` com `grid-template-columns: max-content 1fr`. Em telas estreitas, isso reservava uma primeira coluna rígida para os rótulos e podia empurrar natureza, prioridade e endereço para fora da área visível. A regra global `.badge { white-space: nowrap }` também dificultava a quebra de status e prioridade.

A correção foi escopada a `.detalhe-pagina`, sem alterar `.grid2` ou `.badge` globalmente:

- em até 640 px, `dl.grid2` passa a ter uma única coluna `minmax(0, 1fr)`;
- `dt` e `dd` recebem espaçamento vertical e quebra de palavra;
- `detalhe-cabecalho`, título e badges passam a aceitar quebra de linha;
- o `.card` do detalhe usa padding menor para aproveitar a largura do celular.

Como `/fila/:id` e `/minhas/:id` renderizam o mesmo `OcorrenciaDetalheView`, uma única regra CSS cobre os dois fluxos sem duplicação.

### 3.8 Responsividade do portal cidadão

As rotas públicas `/`, `/registrar-cidadao`, `/consulta` e `/autenticar` também foram ajustadas para 390 px. A navegação superior passa a empilhar marca, links e seletor de idioma/Login; o hero reduz o padding, alinha os botões em coluna e dimensiona o título animado por variável CSS, sem rolagem interna.

Os cards públicos trocaram estilos inline por classes reutilizáveis: `.pagina.pagina-publico`, `.card.card-publico`, `.consulta-form`, `.publico-acoes` e `.publico-voltar`. Em telas estreitas, `.grid2` e `dl.grid2` viram uma coluna, textos longos quebram linha e o mapa do registro usa altura menor. Todas as regras ficaram escopadas a `.portal-wrap` ou a classes específicas, sem alterar telas internas.

O título animado deixou de depender de `fontSize={52}` fixo na `LandingPage`: o componente recebe `fontSize: var(--hero-title-font-size, 52px)` e a media query define `26px` apenas no portal mobile. O mapa do `SeletorCoordenada` manteve os 300 px anteriores no desktop por CSS, permitindo reduzir para 220 px somente no formulário público.

## 4. Padrões de projeto e princípios usados

### 4.1 Separação de responsabilidades / SRP — padrão principal

É o princípio mais evidente desta entrega, embora não seja um padrão GoF:

| Responsabilidade | Onde ficou |
| --- | --- |
| Listar, filtrar e paginar | `FilaDelegadoPage` e `MinhasOcorrenciasPage` |
| Carregar e agir sobre uma ocorrência | Páginas de detalhe |
| Construir e interpretar URLs | `ocorrenciaDeepLink.ts` |
| Apresentar os dados da ocorrência | `OcorrenciaDetalheView`, componente reaproveitado |
| Aplicar regras de acesso | `RequireRole`, já existente |

Antes, uma página de fila concentrava listagem, aba, detalhe, justificativa, confirmação, arquivamento e prioridade. Agora, uma mudança na listagem não exige mexer nas ações de decisão, e vice-versa.

### 4.2 Módulo de funções puras, com função de fachada

`ocorrenciaDeepLink.ts` funciona como uma fachada fina para regras que estavam espalhadas: montar caminho, limpar parâmetro legado, ler aba e localizar status. Não é uma Fachada GoF clássica, porque não representa um subsistema complexo; o nome útil para a apresentação é “extração de lógica pura” ou “módulo utilitário de navegação”.

O benefício é concreto: a regra pode ser testada com Vitest sem montar componentes, sem jsdom e sem servidor.

### 4.3 Adaptador de compatibilidade

O redirecionamento de `?ocorrencia=` funciona como um adaptador de entrada: o sistema aceita o formato antigo e o traduz para o formato novo antes de entregar a página ao usuário. Assim, notificações emitidas antes da mudança continuam válidas.

### 4.4 Observer — padrão existente, preservado

`useTempoRealListener` continua sendo o observador dos eventos de tempo real na lista da fila. Esta entrega não criou outro Observer nem alterou o canal WebSocket. Apenas removeu da mesma página o estado do detalhe; a reatividade da lista permanece como era.

### 4.5 Composição de componentes

As páginas de detalhe compõem `OcorrenciaDetalheView`, `PainelPrioridade`, `OcorrenciaForm` e `ConfirmDialog`. O componente de apresentação continua sem conhecer rotas ou serviços. Isso é reuso por composição, não um novo padrão estrutural inventado para a entrega.

### Fala sugerida para a apresentação

> “Eu separei a lista do detalhe. Antes, as duas informações dividiam a mesma tela, o que atrapalhava especialmente no celular. Agora existe uma rota própria para o detalhe, com botão de voltar. A listagem ficou responsável só por filtrar e navegar; o detalhe ficou responsável por carregar a ocorrência e executar as ações. Criei também um módulo com funções puras para montar as URLs, então a regra de voltar preservando filtros e aba ficou testável sem navegador. Mantive compatibilidade com links antigos de notificação: eles são redirecionados para a rota nova. Também ajustei as rotas públicas para 390 px, com regras escopadas ao portal e testes de regressão mobile. Em termos de padrões, o principal é Separação de Responsabilidades/SRP; o redirecionamento é um adaptador de compatibilidade; e o Observer de tempo real já existente continua funcionando na lista.”

## 5. Validação

### Automatizada

- `./scripts/verificar.sh`: verde na execução completa anterior; `./scripts/verificar.sh --rapido` verde nesta rodada. Inclui import-linter, ruff, testes de backend com 97% de cobertura, tsc e verificação de resíduos de chat. Flutter foi pulado porque o SDK não está instalado nesta máquina.
- Novo spec Cypress `separacao-lista-detalhe.cy.ts`: 3/3 testes aprovados, incluindo a verificação de colunas do resumo, quebra do badge e ausência de overflow horizontal a 390 px em `/fila/:id` e `/minhas/:id`.
- Novo spec Cypress `portal-cidadao-mobile.cy.ts`: 4/4 testes aprovados em 390 px nas rotas `/`, `/registrar-cidadao`, `/consulta` e `/autenticar`, com textos longos, checagem de `scrollWidth`, `getBoundingClientRect` e tamanho da fonte do título animado.
- `validacao-despacho.cy.ts`: 9/9 aprovados; em uma execução em lote houve uma falha de toast por estado compartilhado, que não se reproduziu ao rodar o spec isolado.
- `registro.cy.ts`: 7/9 aprovados. As duas falhas são dos testes de login pela tela (`cy.loginPelaTela`), alheios a esta entrega; os sete testes de registro e navegação passaram.
- `autenticar.cy.ts`: as asserções funcionais passaram; 3 testes falharam apenas em `cy.screenshot()` por timeout do ambiente headless.
- `apreensoes.cy.ts`: 4/4 aprovados.
- `notificacoes-tempo-real.cy.ts`: 3 falhas de WebSocket/toast já existiam na baseline. A execução comparativa com o código original, feita com stash temporário, teve 4 falhas, então não houve regressão introduzida por esta entrega.

### Manual

1. Com usuário `delegado`, abra `/fila`.
2. Clique em uma ocorrência. Confira URL `/fila/<id>` e detalhe em largura integral.
3. Clique em “Voltar à fila”. Confira que filtros e aba foram preservados.
4. Abra `/fila?ocorrencia=<id>`. Confira o redirecionamento para `/fila/<id>`.
5. Com usuário `agente`, abra `/minhas`, clique em uma ocorrência e confirme `/minhas/<id>`.
6. Em uma ocorrência `Em correção`, use Editar, salvar e reenviar. A página deve permanecer no detalhe.
7. Reduza a janela para 390 px e repita os passos. Não deve existir lista ao lado do detalhe; natureza, prioridade e endereço devem quebrar linha e permanecer totalmente visíveis, sem rolagem horizontal.
8. Sem login, abra `/`, `/registrar-cidadao`, `/consulta` e `/autenticar` a 390 px.
9. Confira que a navegação superior, os botões do hero e o título animado cabem na tela, sem barra horizontal.
10. Em `/consulta` e `/autenticar`, use natureza, endereço e hash longos; rótulos e valores devem aparecer empilhados e legíveis.
