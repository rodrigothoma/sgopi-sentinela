# Sugestões de Funcionalidades — SGOPI Sentinela

> Levantamento feito em 05/10/2026 no branch `matheus-Fastapi` (commit `d86eaac`).
> Os caminhos de backend são relativos a `backend/src/`, salvo indicação contrária.
>
> **Escopo.** Este documento lista **funcionalidades que ainda não existem** e que agregariam valor ao sistema. Ele **não** repete os defeitos já apontados em `ANALISE_TECNICA_2026-10-05.md` e tratados em `CORRECOES_ANALISE_TECNICA_2026-10-05.md`. Quando uma sugestão tem relação com um item dessas análises, isso é indicado.
>
> ⚠️ **Governança (AGENTS.md §1.3).** O MVP canônico é RF01 + RF04 + RF02. Qualquer item abaixo que **não** reforce diretamente esses três requisitos amplia o escopo e **precisa de aprovação explícita da equipe** antes de ser implementado. Cada sugestão traz a coluna **Escopo** para facilitar essa decisão:
> - **MVP**: reforça RF01, RF04 ou RF02;
> - **RNF**: atende um requisito não funcional já documentado (RNF01–RNF05);
> - **Extra**: amplia um módulo extra ou cria um novo.

---

## 0. Como ler este documento

As sugestões estão em **ordem crescente de custo de implementação** (da mais fácil para a mais difícil). Para cada uma, há duas notas:

| Nota | Escala | O que mede |
|---|---|---|
| **Custo** | 1 (horas) → 5 (várias sprints) | Esforço de desenvolvimento, quantidade de camadas tocadas (domínio, aplicação, adapters, migração, frontend), novas dependências e risco de regressão |
| **Impacto** | 1 (cosmético) → 5 (muda a operação) | Ganho para o usuário final (agente, delegado, operador), para a confiabilidade/segurança ou para a avaliação acadêmica do projeto |

A coluna **Razão I/C** (impacto ÷ custo) ajuda a achar os "ganhos rápidos": quanto maior, melhor o retorno.

### 0.1 Quadro geral

| # | Sugestão | Escopo | Custo | Impacto | Razão I/C | Status |
|---|---|---|:---:|:---:|:---:|:---:|
| 1 | Filtros e busca na listagem de ocorrências | MVP (RF01/RF04) | 1 | 4 | **4,0** | ✅ Implementado |
| 2 | Notificar o agente autor quando o Delegado decide | MVP (RF04) | 1 | 4 | **4,0** | ✅ Implementado |
| 3 | Exportação CSV de listagens e da trilha de auditoria | RNF03 | 1 | 3 | 3,0 | ✅ Implementado |
| 4 | Atalhos de teclado e contadores na Fila do Delegado | MVP (RF04) | 1 | 2 | 2,0 | Pendente |
| 5 | Indicador de "posição GPS desatualizada" no mapa | MVP (RF02) / RNF04 | 1 | 3 | 3,0 | Pendente |
| 6 | Troca de senha pelo próprio usuário + política de senha | RNF02 | 2 | 4 | 2,0 | Pendente |
| 7 | Prioridade / gravidade da ocorrência | MVP (RF01/RF04/RF02) | 2 | 5 | **2,5** | ✅ Implementado |
| 8 | Comparação de versões (diff) na correção | MVP (RF04) / RNF03 | 2 | 4 | 2,0 | Pendente |
| 9 | Visão tabular do painel tático (contingência do mapa) | MVP (RF02) / RNF04 | 2 | 4 | 2,0 | Pendente |
| 10 | Logout com revogação + renovação de token | RNF02 | 2 | 4 | 2,0 | Pendente |
| 11 | Painel de indicadores (KPIs) operacionais | MVP (RF02/RF04) | 2 | 4 | 2,0 | ✅ Implementado |
| 12 | Linha do tempo unificada da ocorrência | MVP (RF01) / RNF03 | 2 | 3 | 1,5 | ✅ Implementado |
| 13 | Gestão de usuários (CRUD lógico) pelo Supervisor | RNF02 | 3 | 4 | 1,3 | ✅ Implementado |
| 14 | Alertas automáticos de criticidade (gatilhos do RF05) | Extra (RF05) | 3 | 4 | 1,3 | Pendente |
| 15 | Assinatura digital do laudo (validação prevista no RF07) | Extra (RF07) | 3 | 3 | 1,0 | Pendente |
| 16 | Encadeamento de hash na auditoria (*hash chain*) | RNF03 | 3 | 4 | 1,3 | Pendente |
| 17 | Observabilidade: métricas, *health* detalhado e rastreamento | RNF01/RNF04 | 3 | 3 | 1,0 | Pendente |
| 18 | Empacotamento em contêineres (Dockerfile + compose completo) | RNF05 | 2 | 3 | 1,5 | Pendente |
| 19 | Despacho por tempo de rota (ETA) em vez de linha reta | MVP (RF02) | 4 | 4 | 1,0 | Pendente |
| 20 | Outbox de eventos + fila de trabalhos em segundo plano | RNF01/RNF04 | 4 | 4 | 1,0 | Pendente |
| 21 | Aplicativo de campo do agente (PWA com modo offline) | MVP (RF01/RF02) | 5 | 5 | 1,0 | Pendente |
| 22 | Escalonamento horizontal (Redis para WS, limitadores e cache) | RNF01 | 4 | 3 | 0,75 | Pendente |
| 23 | Ciclo de vida de dados pessoais (LGPD) | RNF02 | 4 | 4 | 1,0 | Pendente |
| 24 | Autenticação forte (MFA / SSO institucional) | RNF02 | 4 | 3 | 0,75 | Pendente |

> **Ganhos rápidos recomendados** (maior razão I/C e dentro do MVP): **#1, #2, #7, #5, #9**.
>
> **Andamento (05/10/2026):** #1, #2, #3, #7, #11, #12 e #13 implementados — ver o bloco **Status** de cada item.

---

## 1. Nível 1 — Baixo custo (horas a 1 dia)

### #1. Filtros e busca na listagem de ocorrências
| Escopo | Custo | Impacto |
|---|:---:|:---:|
| MVP (RF01/RF04) | 1 | 4 |

**Situação atual.** `FiltroOcorrencias` (`application/ports/outbound/repositorio_ocorrencia.py:17`) aceita apenas `status`, `agente_policial_id`, `limit` e `offset`. Não há como buscar por protocolo, natureza, período do fato ou texto do relato. Com o gerador de ocorrências de demonstração ligado, a fila e "Minhas ocorrências" crescem rápido e ficam difíceis de navegar.

**Proposta.**
- Estender o DTO `FiltroOcorrencias` com: `natureza`, `protocolo`, `data_fato_de`, `data_fato_ate`, `origem` (`POLICIAL`/`PUBLICA`) e `texto` (busca em `descricao`/`localizacao`).
- No adapter SQLAlchemy, traduzir para `WHERE` com `ILIKE` (portável entre PostgreSQL e SQLite). Em Postgres, opcionalmente usar `pg_trgm` depois.
- Expor os filtros como `Query(...)` tipados em `GET /v1/ocorrencias`.
- No frontend, uma barra de filtros reutilizável em `FilaDelegadoPage` e `MinhasOcorrenciasPage`, com os filtros na *query string* da URL (permite compartilhar o link).

**Arquivos tocados.** `repositorio_ocorrencia.py`, `ocorrencia_repositorio_sqlalchemy.py`, `consultar_ocorrencias.py`, `ocorrencias_router.py`, as duas páginas, `ocorrenciasService.ts` e os arquivos de i18n.

**Riscos.** Baixos. Atenção ao RBAC: o filtro `agente_policial_id` continua forçado para o papel AGENTE.

**Status: ✅ Implementado (05/10/2026).**
- `FiltroOcorrencias` e `ListarOcorrenciasInput` ganharam `natureza`, `protocolo`, `texto`, `origem`, `data_fato_de` e `data_fato_ate`. O caso de uso (`montar_filtro` em `consultar_ocorrencias.py`) trata termo vazio como "sem filtro", interpreta data sem fuso como UTC e devolve 422 para período invertido (`ocorrencia.periodo_invalido`) e origem desconhecida (`ocorrencia.origem_invalida`). O RBAC continua igual: o Agente só vê as próprias ocorrências, com ou sem filtro.
- No adapter SQLAlchemy a busca usa `ILIKE` com os curingas do usuário (`%`, `_`) tratados como literais. Isso funciona tanto no PostgreSQL quanto no SQLite. O fake em memória honra o mesmo contrato.
- `GET /v1/ocorrencias` aceita os novos `Query(...)` (dependência `filtros_listagem`, compartilhada com a exportação do #3).
- No frontend, o componente `FiltrosOcorrenciasBar` e o hook `useFiltrosOcorrenciasUrl` foram adicionados à fila do Delegado (com filtro de origem) e a "Minhas ocorrências". Os filtros ficam na *query string* (`texto`, `protocolo`, `natureza`, `origem`, `de`, `ate`), então o link pode ser compartilhado. Textos em pt/en.
- Testes: unitários em `test_consultar_ocorrencias.py`, integração em `test_sugestoes_busca_notificacao_exportacao.py` e `utils/__tests__/filtrosOcorrencias.test.ts`.

---

### #2. Notificar o agente autor quando o Delegado decide
| Escopo | Custo | Impacto |
|---|:---:|:---:|
| MVP (RF04) | 1 | 4 |

**Situação atual.** O módulo de notificações (`domain/notificacao/`, `NotificationBell.tsx`) já existe, mas a validação, a devolução para correção e a rejeição **não** notificam o agente que lavrou a ocorrência. Esse ponto foi citado na análise anterior como "notificação ao agente autor" e ficou fora da rodada de correções. Hoje o agente precisa abrir "Minhas ocorrências" para descobrir que tem uma correção pendente.

**Proposta.**
- Em `revisar_ocorrencia.py`, após a transição de estado, criar uma `Notificacao` endereçada ao `agente_policial_id`, com o tipo (`VALIDADA`, `DEVOLVIDA`, `REJEITADA`), a justificativa e o link para o detalhe.
- Publicar o evento no WebSocket já filtrado por audiência (`adapters/inbound/websocket/audiencia.py`), de modo que só o autor o receba.
- Não notificar ocorrências de origem `PUBLICA` (o "autor" é o usuário de sistema `CIDADAO`).

**Arquivos tocados.** `revisar_ocorrencia.py`, `di.py` (injetar `RepositorioNotificacao`), testes unitários do caso de uso.

**Riscos.** Mínimos. A porta e o repositório já existem.

**Status: ✅ Implementado (05/10/2026).**
- `ValidarOcorrencia`, `DevolverParaCorrecao` e `RejeitarOcorrencia` recebem `RepositorioNotificacao` (injetado em `di.py`). A notificação pessoal do novo tipo `REVISAO_OCORRENCIA` é gravada **na mesma transação** da decisão. Depois do commit, o evento `NOTIFICACAO_EMITIDA` é publicado, e a audiência do WebSocket o entrega só ao autor (`usuario_id`).
- O título traz o protocolo e a mensagem traz a natureza e a justificativa ou despacho. A prioridade é ALTA para devolução, MÉDIA para rejeição e BAIXA para validação. O link `/minhas?protocolo=…&ocorrencia=…` abre o detalhe já filtrado.
- Não há notificação para ocorrências de origem `PUBLICA`, nem para arquivamento ou exclusão (que reutilizam a mesma base).
- O evento passou a ser montado por uma fábrica única, `domain/notificacao/eventos.py`, reaproveitada por `CriarNotificacaoUseCase`.
- Frontend: o sino agora lê o campo `link` devolvido pela API. Antes ele lia `link_acao`, que não existe, e por isso o redirecionamento nunca acontecia. O sino também ganhou ícone e rota para o novo tipo.
- Testes: `test_notificar_autor_revisao.py` (unitário) e o teste de integração do item #1.

---

### #3. Exportação CSV de listagens e da trilha de auditoria
| Escopo | Custo | Impacto |
|---|:---:|:---:|
| RNF03 | 1 | 3 |

**Situação atual.** A trilha de auditoria (`TrilhaAuditoriaPage`) e as listagens só existem na tela. Corregedoria e controle externo costumam pedir os registros em planilha.

**Proposta.**
- Endpoint `GET /v1/auditoria/exportar?formato=csv` (e o equivalente em ocorrências), gerando `StreamingResponse` com `text/csv; charset=utf-8` e BOM para o Excel.
- A geração de CSV fica **no adapter HTTP**: o caso de uso continua devolvendo DTOs.
- **Auditar a própria exportação** (quem exportou, quais filtros, quantas linhas). Exportar em massa é um ato sensível.
- Aplicar a mesma máscara de CPF que os logs já usam (`infrastructure/logging.py`).

**Riscos.** Vazamento de PII se a máscara for esquecida. Restringir a DELEGADO/SUPERVISOR.

**Status: ✅ Implementado (05/10/2026).**
- `GET /v1/auditoria/exportar?formato=csv` (mesmos filtros da consulta) e `GET /v1/ocorrencias/exportar?formato=csv` (mesmos filtros do #1, até 5 000 linhas, percorrendo a listagem paginada). As duas rotas são restritas a DELEGADO e SUPERVISOR.
- O CSV é gerado **no adapter HTTP** (`adapters/inbound/http/exportacao_csv.py`): `StreamingResponse` em `text/csv; charset=utf-8`, com BOM e separador `;` para abrir direto no Excel em pt-BR. Toda célula passa por `mascarar_cpfs` (a mesma regra dos logs), e textos iniciados por `= + - @` recebem apóstrofo para neutralizar injeção de fórmula.
- **A própria exportação é auditada:** o novo caso de uso `RegistrarExportacao` grava `auditoria.exportar` ou `ocorrencias.exportar`, com autor, IP, filtros aplicados e total de linhas.
- Frontend: botão "Exportar CSV" na fila do Delegado (aba e busca atuais) e na Trilha de Auditoria (filtros de operação e entidade). As novas operações aparecem com rótulo na trilha.
- Testes: `test_registrar_exportacao.py`, `test_exportacao_csv.py` e o teste de integração do item #1 (RBAC, conteúdo, máscara de CPF e registro na auditoria).

---

### #4. Atalhos de teclado e contadores na Fila do Delegado
| Escopo | Custo | Impacto |
|---|:---:|:---:|
| MVP (RF04) | 1 | 2 |

**Proposta.**
- Contadores no topo da fila: aguardando revisão, em correção, validadas hoje e tempo médio de espera.
- Atalhos de teclado: `J`/`K` para navegar, `V` para validar, `D` para devolver e `Esc` para fechar o modal. Exibir a legenda com `?`.
- Destacar a ocorrência que está na fila há mais de N horas (constante de domínio, sem número mágico).

**Arquivos tocados.** Somente o frontend (`FilaDelegadoPage.tsx` e i18n). Os contadores podem sair de `GET /v1/ocorrencias?status=...` com `limit=1`, lendo o campo `total`.

---

### #5. Indicador de "posição GPS desatualizada" no mapa
| Escopo | Custo | Impacto |
|---|:---:|:---:|
| MVP (RF02) / RNF04 | 1 | 3 |

**Situação atual.** O domínio já calcula a idade da posição (`Posicao.idade`, `domain/viatura/entity.py`) e o despacho descarta posições acima de `max_idade`. O mapa, porém, desenha a viatura do mesmo jeito com uma posição de 5 segundos ou de 10 minutos.

**Proposta.**
- No `MapaTatico.tsx`, aplicar estilos por faixa de idade: normal (< 30 s), atenuado (30 s – 2 min) e tracejado com "⚠ sem sinal há X min" (> 2 min).
- Expor as faixas em uma constante compartilhada (por exemplo, devolvida em `GET /v1/viaturas`), e não fixa no frontend.
- Na lista de sugestões de despacho, mostrar "última posição há X" quando a viatura for elegível só pela posição antiga (contingência do RNF04: "seleção manual por última posição conhecida").

---

## 2. Nível 2 — Custo moderado (1 a 3 dias)

### #6. Troca de senha pelo próprio usuário + política de senha
| Escopo | Custo | Impacto |
|---|:---:|:---:|
| RNF02 | 2 | 4 |

**Situação atual.** A autenticação tem apenas `POST /v1/auth/login` e `GET /v1/auth/me`. Todos os usuários do seed usam `Senha@123` e não há como trocá-la. A análise anterior também citou "política de senha" como item em aberto.

**Proposta.**
- Caso de uso `AlterarSenha` (senha atual + nova), usando a porta `HasherSenha` já existente.
- Value object `SenhaForte` no domínio (comprimento mínimo, classes de caracteres, recusa de senha igual ao login), com chaves de i18n.
- Flag `deve_trocar_senha` no usuário: forçar a troca no primeiro login (útil para os usuários do seed e para o item #13).
- Auditar a troca, **sem** registrar nenhum valor de senha.

**Arquivos tocados.** `domain/usuario/entity.py`, novo caso de uso em `use_cases/auth/`, `auth_router.py`, migração (coluna `deve_trocar_senha`) e uma tela "Minha conta" no frontend.

---

### #7. Prioridade / gravidade da ocorrência
| Escopo | Custo | Impacto |
|---|:---:|:---:|
| MVP (RF01/RF04/RF02) | 2 | 5 |

**Situação atual.** A entidade `Ocorrencia` (`domain/ocorrencia/entity.py:158`) não tem nenhum atributo de prioridade. A fila do Delegado é ordenada só por antiguidade (`mais_recentes_primeiro=False`), e o despacho trata um furto antigo e um roubo em andamento do mesmo jeito. Isso já havia sido citado como "gravidade na fila do Delegado".

**Proposta.**
- Enum de domínio `PrioridadeOcorrencia` (`BAIXA`, `MEDIA`, `ALTA`, `URGENTE`), com valor **sugerido** a partir da natureza ou das tipificações (tabela de regras pura no domínio) e **ajustável** pelo agente no registro e pelo Delegado na revisão.
- A fila do Delegado ordena por (prioridade desc, antiguidade asc).
- O orquestrador de despacho atende primeiro as ocorrências `URGENTE`/`ALTA`.
- Badge de prioridade no `StatusBadge`, no mapa e no detalhe.
- Toda mudança de prioridade feita pelo Delegado entra na auditoria com justificativa.

**Arquivos tocados.** Domínio, DTOs de entrada/saída, migração, repositório, `revisar_ocorrencia.py`, `orquestrador_despacho.py`, formulário e fila no frontend. **Atualizar o diagrama de classes e o UC01/UC04** (`docs/diagramas/`).

**Por que o impacto é 5.** É o único item que melhora ao mesmo tempo os três requisitos do MVP: o registro (RF01), a triagem (RF04) e o despacho (RF02).

**Status: ✅ Implementado (05/10/2026).**
- **Domínio:** o novo `domain/ocorrencia/prioridade.py` traz o enum `PrioridadeOcorrencia` (`BAIXA`, `MEDIA`, `ALTA`, `URGENTE`, cada um com `peso`) e a tabela de regras pura `sugerir_prioridade`. A regra procura termos, sem acento, na natureza e nas tipificações (artigo e descrição), em pt e en. Por exemplo: homicídio ou art. 121 → URGENTE; roubo ou art. 157 → ALTA; perda ou extravio → BAIXA. Sem nenhuma regra aplicável, a prioridade é MEDIA.
- **Registro:** `Ocorrencia.registrar` aceita a prioridade escolhida pelo agente; se ela vier vazia, usa a sugerida. A auditoria do registro anota a prioridade e se ela foi sugerida.
- **Redefinição pelo Delegado:** `Ocorrencia.redefinir_prioridade` exige justificativa (mínimo 10 caracteres), recusa repetir a prioridade atual e só vale enquanto a ocorrência ainda está em fluxo (`ESTADOS_PRIORIZAVEIS`).
- **Caso de uso e rota:** o novo caso de uso `RedefinirPrioridade` responde em `POST /v1/ocorrencias/{id}/prioridade` (somente DELEGADO). Ele audita `ocorrencia.redefinir_prioridade` com a prioridade anterior, a nova e a justificativa, e publica `OcorrenciaPrioridadeAlterada` no WebSocket.
- **Ordenação:** `FiltroOcorrencias.ordenar_por_prioridade` ordena por gravidade decrescente e, dentro da mesma gravidade, pela mais antiga. No SQL isso é um `CASE` sobre o peso. O parâmetro aparece em `GET /v1/ocorrencias` como `ordenar_por_prioridade`.
- **Fila e despacho:** a fila do Delegado e o painel tático usam essa ordenação. O orquestrador de despacho automático também, então com uma viatura só a URGENTE é atendida antes da MEDIA mais antiga.
- **Migração `0017`:** cria a coluna `ocorrencias.prioridade` (padrão MEDIA, com índice) e preenche as ocorrências existentes com a mesma regra do domínio. Foi testada com upgrade, preenchimento e downgrade em SQLite.
- **Frontend:**
  - seletor opcional "Prioridade" no registro (padrão "Automática"), e a prioridade atribuída aparece na confirmação;
  - `PrioridadeBadge`, com forma do marcador e rótulo além da cor, na fila, em "Minhas ocorrências", no painel tático e no detalhe;
  - painel "Alterar prioridade" para o Delegado;
  - gravidade no tooltip do mapa, com marcador URGENTE à frente dos demais.
- **Pendente:** o diagrama de classes e o UC01/UC04 em `docs/diagramas/` ainda não foram atualizados.
- **Testes:** `test_prioridade_ocorrencia.py`, `test_redefinir_prioridade.py`, um teste novo em `test_orquestrador_despacho.py` e o teste de integração `test_sugestoes_prioridade_indicadores_linha_do_tempo_usuarios.py`.

---

### #8. Comparação de versões (diff) na correção
| Escopo | Custo | Impacto |
|---|:---:|:---:|
| MVP (RF04) / RNF03 | 2 | 4 |

**Situação atual.** Quando o agente reenvia uma ocorrência devolvida, o Delegado vê só a versão nova. A análise anterior registrou que a "auditoria de correção [é] sem diff completo".

**Proposta.**
- Em `corrigir_ocorrencia.py`, gravar na auditoria um *snapshot* estruturado dos campos alterados (antes → depois) para narrativa, local, natureza, tipificações e envolvidos.
- Endpoint `GET /v1/ocorrencias/{id}/versoes` que reconstrói as versões a partir da auditoria (append-only, compatível com o RNF03).
- No detalhe da ocorrência, uma aba "Alterações" com diff lado a lado, destacando o que mudou desde a devolução.

**Riscos.** O volume da auditoria aumenta. Guardar só os campos alterados.

---

### #9. Visão tabular do painel tático (contingência do mapa)
| Escopo | Custo | Impacto |
|---|:---:|:---:|
| MVP (RF02) / RNF04 | 2 | 4 |

**Situação atual.** O RNF04 exige: "em falha no mapa, exibe-se a listagem tabular". O `PainelTaticoPage` depende do Leaflet e dos *tiles* do OpenStreetMap. Se o servidor de *tiles* cair ou a rede bloquear o domínio, o operador perde a visão da frota.

**Proposta.**
- Alternador "Mapa | Tabela" no painel tático, mais a troca automática para "Tabela" quando o carregamento de *tiles* falhar N vezes (evento `tileerror` do Leaflet).
- Tabela de viaturas (prefixo, situação, idade da posição, ocorrência atual) e de ocorrências validadas sem atendimento, com o botão **Despachar** usando as mesmas sugestões por proximidade.
- Atualização pelo mesmo WebSocket (`useTempoReal`).

**Valor acadêmico.** Fecha um RNF que hoje está documentado mas não implementado.

---

### #10. Logout com revogação + renovação de token
| Escopo | Custo | Impacto |
|---|:---:|:---:|
| RNF02 | 2 | 4 |

**Situação atual.** Não há rota de logout nem *refresh token*. Um JWT vazado continua válido até expirar, e desativar um usuário não derruba a sessão dele.

**Proposta.**
- *Access token* curto (5–15 min) e *refresh token* opaco, rotativo e guardado com hash numa tabela `sessoes`.
- `POST /v1/auth/renovar` e `POST /v1/auth/sair`, este último revogando a sessão.
- Revogar todas as sessões do usuário ao desativá-lo (#13) ou ao trocar a senha (#6).
- No WebSocket, encerrar a conexão quando a sessão for revogada. A análise anterior apontou que o token só é validado no *handshake*.
- Nova porta `RepositorioSessao` e adapter SQLAlchemy. O frontend ganha um interceptor do axios para renovar o token de forma transparente.

---

### #11. Painel de indicadores (KPIs) operacionais
| Escopo | Custo | Impacto |
|---|:---:|:---:|
| MVP (RF02/RF04) | 2 | 4 |

**Situação atual.** A `InicioPage` mostra listas (viaturas, efetivo, ocorrências), mas não há métricas de desempenho.

**Proposta.** Um caso de uso `CalcularIndicadores` (somente leitura) que devolve, para um período:
- **RF04**: tempo médio entre o registro e a decisão do Delegado; taxa de devolução e de rejeição.
- **RF02**: tempo médio entre a validação e o despacho e entre o despacho e o encerramento; viaturas por situação ao longo do dia.
- **RF01**: ocorrências por natureza, por origem (policial × pública) e por faixa horária.

A tela usa gráficos simples (barras e linha). Todos os dados já existem em `historico_status_ocorrencia` e `ordens_despacho`, então **não é preciso migração**.

**Riscos.** Consultas agregadas pesadas. Fazer a agregação no SQL, e não em Python após um `LIMIT` (problema já visto em interagências).

**Status: ✅ Implementado (05/10/2026).**
- **Backend:**
  - a porta de saída `ConsultaIndicadores` é implementada por `IndicadoresSQLAlchemy`, e **toda agregação roda no banco** (`GROUP BY`, `AVG`, `COUNT`, subconsultas de primeira transição e primeiro despacho);
  - diferença entre datas e hora do dia são montadas por dialeto: `EXTRACT(EPOCH/HOUR)` no PostgreSQL, `julianday`/`strftime` no SQLite;
  - o caso de uso `CalcularIndicadores` (DELEGADO, SUPERVISOR e OPERADOR_CENTRAL) valida o período (padrão de 30 dias, máximo de 366) e o fuso IANA, converte as faixas horárias de UTC para a hora local e agrupa as naturezas além da 10ª em "OUTRAS";
  - não houve migração.
- **Endpoint:** `GET /v1/indicadores?de=&ate=&fuso=`.
- **Métricas RF04:** tempo médio do registro até a primeira decisão do Delegado; contagem de validadas, devolvidas e rejeitadas; taxas de devolução e de rejeição.
- **Métricas RF02:** tempo médio da validação até o primeiro despacho e do despacho até o encerramento; despachos por faixa horária.
- **Métricas RF01:** ocorrências por natureza, por origem e por faixa horária (hora do fato).
- **Frota:** só existe o **retrato atual** por situação. A situação da viatura não tem série histórica gravada, então "viaturas por situação ao longo do dia" exigiria guardar esse histórico, o que fica fora deste item.
- **Frontend:**
  - página "Indicadores" (`/indicadores`) com seletor de 7, 30 ou 90 dias, seis cartões de KPI, barras horizontais e colunas por hora em SVG;
  - os gráficos são de série única, na cor primária do tema, validada nos temas claro e escuro;
  - cada gráfico tem tooltip ao passar o mouse e a opção "Ver como tabela";
  - a página foi conferida em navegador sem rolagem horizontal em 390px.
- **Testes:** `test_calcular_indicadores.py` e o teste de integração do item #7, que verifica as agregações reais no SQLite.

---

### #12. Linha do tempo unificada da ocorrência
| Escopo | Custo | Impacto |
|---|:---:|:---:|
| MVP (RF01) / RNF03 | 2 | 3 |

**Proposta.** Uma aba "Linha do tempo" no `OcorrenciaDetalhe` que junta em ordem cronológica:
- as transições de status (`historico_status`);
- os despachos e encerramentos (ordens);
- as evidências anexadas e as verificações de integridade;
- os itens apreendidos e as movimentações de custódia;
- o vínculo a inquérito e as solicitações de laudo.

Um endpoint `GET /v1/ocorrencias/{id}/linha-do-tempo` monta a sequência a partir dos repositórios existentes. É útil para o Delegado e para a demonstração.

**Status: ✅ Implementado (05/10/2026).**
- O caso de uso `MontarLinhaDoTempo` aplica a mesma política de acesso do detalhe da ocorrência. Ele junta, em ordem cronológica:
  - transições de status, com justificativa;
  - ordens de despacho (com o prefixo da viatura e se foram de apoio) e o encerramento de cada uma;
  - evidências anexadas;
  - verificações de integridade, lidas da auditoria `evidencia.verificar_integridade`;
  - itens apreendidos e movimentações de custódia;
  - vínculo a inquérito, datado pela auditoria do inquérito ou, na falta dela, pela abertura do inquérito;
  - laudos solicitados e concluídos.
- Cada evento traz quem fez (`por_id` e `por_nome`). Datas sem fuso (SQLite) são normalizadas para UTC antes de ordenar. Somente leitura, sem tabela nova.
- **Endpoint:** `GET /v1/ocorrencias/{id}/linha-do-tempo`.
- **Frontend:** nova aba "Linha do tempo" no detalhe da ocorrência (`LinhaDoTempoAba`). Ela recarrega junto com o detalhe sempre que a versão da ocorrência muda.
- **Testes:** o teste de integração do item #7 percorre registro, apreensão, evidência, integridade, validação, despacho e encerramento, e confere a presença e a ordem dos eventos e o controle de acesso.

---

## 3. Nível 3 — Custo relevante (3 dias a 1 sprint)

### #13. Gestão de usuários (CRUD lógico) pelo Supervisor
| Escopo | Custo | Impacto |
|---|:---:|:---:|
| RNF02 | 3 | 4 |

**Situação atual.** `usuarios_router.py` expõe apenas `GET /v1/usuarios`. Os usuários só nascem pelo seed. O enum `Papel` tem `ESCRIVAO`, que não é usado em lugar nenhum, e a análise anterior notou que o seed não tem PERITO/SUPERVISOR.

**Proposta.**
- Casos de uso: `CadastrarUsuario`, `AlterarPapel`, `DesativarUsuario` (com `ativo = false`, nunca `DELETE`, conforme AGENTS.md §5) e `ReativarUsuario`.
- Somente o SUPERVISOR pode executá-los. Ninguém altera o próprio papel.
- Senha provisória com `deve_trocar_senha = true` (#6).
- Auditar tudo, com o papel anterior e o novo.
- Uma tela "Efetivo" com a tabela de usuários e as ações.

**Dependências.** #6 e, de preferência, #10 (revogar sessões ao desativar).

**Status: ✅ Implementado (05/10/2026), sem a senha provisória obrigatória.**
- **Domínio:** `Usuario.cadastrar` valida o login (3 a 50 caracteres: minúsculas, dígitos, `.`, `_` e `-`). Também foram criados `alterar_papel`, `desativar` e `reativar`. O usuário de sistema `CIDADAO` não pode ser gerido nem atribuído.
- **Casos de uso:** `ListarUsuariosGestao`, `CadastrarUsuario`, `AlterarPapelUsuario`, `DesativarUsuario` e `ReativarUsuario`.
  - Só o SUPERVISOR e o OPERADOR_CENTRAL podem executá-los (o Operador foi incluído depois, a pedido da equipe), e ninguém age sobre a própria conta (`usuario.proprio`).
  - Login duplicado retorna 409.
  - Não existe `DELETE`: a retirada é `ativo = false`.
  - Tudo é auditado com o estado anterior e o novo (`usuario.cadastrar`, `usuario.alterar_papel`, `usuario.desativar`, `usuario.reativar`), sem senha na trilha.
- **Rotas:** `GET /v1/usuarios/gestao`, `POST /v1/usuarios`, `PATCH /v1/usuarios/{id}/papel`, `POST /v1/usuarios/{id}/desativar` e `POST /v1/usuarios/{id}/reativar`.
- **Sessões (substitui o #10 neste ponto):** a checagem por requisição (`exigir_usuario_ativo`) agora também compara o papel do token com o do cadastro. Desativar alguém ou trocar seu papel derruba a sessão aberta na requisição seguinte (401).
- **Seed:** o seed passou a criar o usuário `supervisor` (SUPERVISOR); sem ele ninguém conseguiria usar a gestão.
- **Frontend:** página "Efetivo" (`/efetivo`, para SUPERVISOR e OPERADOR_CENTRAL) com:
  - formulário de cadastro com senha inicial;
  - tabela com troca de papel, desativação e reativação, todas confirmadas antes de executar;
  - filtro de inativos;
  - controles bloqueados na linha do próprio usuário logado.
- **Fora deste item:** `deve_trocar_senha = true` e a política de senha dependem do #6, que não foi implementado. Por enquanto a senha inicial é definida pelo Supervisor (mínimo de 8 caracteres), e o usuário não é obrigado a trocá-la.
- **Testes:** `test_gerir_usuarios.py` e o teste de integração do item #7, que cobre o fluxo completo, incluindo a queda da sessão após a troca de papel e o login recusado do usuário desativado.

---

### #14. Alertas automáticos de criticidade (gatilhos do RF05)
| Escopo | Custo | Impacto |
|---|:---:|:---:|
| Extra (RF05) | 3 | 4 |

**Situação atual.** O RF05 especifica "alertas **automáticos** para supervisores baseados em gatilhos de alta criticidade (**reincidência de suspeitos na semana** ou **aumento expressivo de crimes em área geográfica num intervalo de 24h**)". Hoje o alerta é **manual** (`POST /v1/inteligencia/alertas-criticidade/emitir`). A palavra "reincidência" só aparece no gerador de demonstração.

**Proposta.**
- Dois detectores puros no domínio:
  - `DetectorReincidencia`: o mesmo documento de suspeito em ≥ N ocorrências validadas em 7 dias;
  - `DetectorPicoRegional`: um *cluster* (o agrupamento de `calcular_areas_risco.py` já existe) cujo volume em 24 h passa X vezes a média móvel.
- Um caso de uso `AvaliarGatilhosCriticidade`, chamado após cada validação (RF04) e por uma tarefa periódica.
- Deduplicação: não emitir de novo o mesmo alerta para o mesmo suspeito ou área dentro da janela.
- Os limiares ficam em constantes de domínio ou no `Settings`, nunca como números mágicos.

**Atenção.** É extra: precisa de aprovação. Ainda assim, fecha uma lacuna entre o que o RF05 documenta e o que foi implementado.

---

### #15. Assinatura digital do laudo (validação prevista no RF07)
| Escopo | Custo | Impacto |
|---|:---:|:---:|
| Extra (RF07) | 3 | 3 |

**Situação atual.** O RF07 fala em "anexação segura de laudos [...] **com validação de assinatura digital**". A entidade `Laudo` guarda só o `hash_sha256` do arquivo, que garante integridade, mas não autoria.

**Proposta.**
- Porta `VerificadorAssinatura` com um adapter que valida a assinatura PAdES (PDF assinado) e extrai o titular e a validade do certificado.
- Guardar no laudo: `assinado_por`, `certificado_emissor`, `assinado_em` e o resultado da verificação.
- Recusar o anexo (ou marcá-lo como "não assinado") conforme uma regra de domínio.
- Para a demonstração, um certificado autoassinado de uma "AC de teste". Em produção, a cadeia ICP-Brasil.

**Riscos.** Bibliotecas de PDF/X.509 adicionam dependências. Elas ficam **só no adapter**, nunca no domínio.

---

### #16. Encadeamento de hash na auditoria (*hash chain*)
| Escopo | Custo | Impacto |
|---|:---:|:---:|
| RNF03 | 3 | 4 |

**Situação atual.** `registros_auditoria` é append-only por convenção e por *trigger*, mas um DBA com acesso direto poderia alterar ou remover uma linha sem deixar rastro detectável.

**Proposta.**
- Cada registro guarda `hash_anterior` e `hash_registro = SHA-256(hash_anterior ‖ conteúdo canônico)`. A canonicalização deve ser determinística (a mesma lição do `hash_narrativa` v2).
- Um caso de uso `VerificarCadeiaAuditoria` percorre a cadeia e aponta o primeiro elo quebrado. Expô-lo para o SUPERVISOR e rodá-lo periodicamente.
- Opcional: publicar o hash do último elo do dia (a "âncora") num local externo, ou imprimi-lo no relatório diário.

**Riscos.** Inserções concorrentes precisam ser serializadas para manter a cadeia linear (bloqueio de linha, `SELECT ... FOR UPDATE` na âncora, ou uma sequência). Exige uma migração que calcule os hashes do histórico existente.

---

### #17. Observabilidade: métricas, *health* detalhado e rastreamento
| Escopo | Custo | Impacto |
|---|:---:|:---:|
| RNF01/RNF04 | 3 | 3 |

**Situação atual.** Há logs JSON com `request_id` e máscara de CPF (bom ponto de partida) e um `/health` simples. Não há métricas nem rastreamento.

**Proposta.**
- `/health/ready` que verifica o banco, o armazenamento de arquivos e o SMTP; `/health/live` continua simples.
- Métricas no formato Prometheus: latência por rota, conexões WebSocket ativas, posições GPS recebidas e rejeitadas, idade média da posição, tamanho da fila do Delegado, falhas de e-mail.
- OpenTelemetry para rastrear requisição → caso de uso → banco.
- Tudo isso fica em `adapters/` e `infrastructure/`; o domínio não muda.

---

### #18. Empacotamento em contêineres (Dockerfile + compose completo)
| Escopo | Custo | Impacto |
|---|:---:|:---:|
| RNF05 | 2 | 3 |

> Custo baixo, mas listado aqui porque só rende de verdade junto com #17 e #22.

**Situação atual.** O `docker-compose.yml` sobe só o PostgreSQL. O backend e o frontend rodam na máquina do desenvolvedor.

**Proposta.**
- `backend/Dockerfile` *multi-stage* com `uv` (imagem final *slim*, usuário não root) e um *entrypoint* que roda `alembic upgrade head`.
- `frontend/Dockerfile` que faz o build com Vite e serve o resultado com Nginx (com cabeçalhos CSP e *proxy* para `/v1` e para o WebSocket).
- Um perfil `demo` no compose que sobe tudo e roda o seed: `docker compose --profile demo up`.
- Um job no CI que constrói as imagens.

**Valor.** A banca ou um colega roda o sistema inteiro com um comando.

---

## 4. Nível 4 — Alto custo (1 a 2 sprints)

### #19. Despacho por tempo de rota (ETA) em vez de linha reta
| Escopo | Custo | Impacto |
|---|:---:|:---:|
| MVP (RF02) | 4 | 4 |

**Situação atual.** `sugerir_viaturas_proximas` (`domain/despacho/servico_proximidade.py`) ordena pela distância Haversine. Em áreas com rio, rodovia ou ruas de mão única, a viatura mais próxima em linha reta pode estar bem mais longe pela rua. O simulador já tem um `roteador.py`, mas ele é usado só para animar o trajeto.

**Proposta.**
- Porta `CalculadoraRota` em `application/ports/outbound/`, com dois adapters:
  - `CalculadoraRotaHaversine`, o comportamento atual e *fallback*;
  - `CalculadoraRotaOSRM`, que consulta um OSRM **auto-hospedado**, para não enviar a localização do crime a um terceiro (ver N8 da análise).
- O caso de uso faz uma pré-seleção das K viaturas mais próximas por Haversine (barato) e só calcula o ETA real dessas K.
- Timeout curto e *fallback* automático para Haversine, com log (RNF04: "timeouts em integrações geram retentativas e logs de erro").
- A interface mostra "≈ 6 min (3,2 km)" em cada sugestão.

**Riscos.** Infraestrutura extra (OSRM + extrato OSM da região) e testes com *fakes* da porta.

---

### #20. Outbox de eventos + fila de trabalhos em segundo plano
| Escopo | Custo | Impacto |
|---|:---:|:---:|
| RNF01/RNF04 | 4 | 4 |

**Situação atual.** E-mails e eventos de WebSocket são publicados depois do `commit`, mas ainda dentro da requisição. Se o processo cair entre o commit e a publicação, o evento se perde. Se o SMTP estiver lento, a requisição fica lenta. A correção anterior listou este item como "mudança arquitetural maior, recomendada e não feita".

**Proposta.**
- Tabela `outbox_eventos`, gravada **na mesma transação** da `UnidadeDeTrabalho`.
- Um *worker* (tarefa `asyncio` no *lifespan* ou processo separado) lê os eventos pendentes, publica no WebSocket, envia o e-mail e marca o evento como entregue, com retentativas e *backoff*.
- Os jobs periódicos (alerta de vencimento de medida protetiva, #14, verificação da cadeia de auditoria #16) passam a rodar nesse mesmo mecanismo, e não mais por chamada HTTP manual (`/verificar-vencimentos`).

**Benefícios.** Entrega garantida "pelo menos uma vez", requisições mais rápidas e uma base para o #22.

---

### #21. Aplicativo de campo do agente (PWA com modo offline)
| Escopo | Custo | Impacto |
|---|:---:|:---:|
| MVP (RF01/RF02) | 5 | 5 |

**Situação atual.** O frontend é uma SPA de desktop. Não há *manifest* nem *service worker* (`frontend/public/` só tem `logo.svg`). Em campo, o agente costuma ter sinal ruim.

**Proposta.**
- Tornar o frontend uma PWA instalável (`vite-plugin-pwa`) com layout móvel para as telas do agente: registrar, minhas ocorrências e ordem de despacho recebida.
- **Rascunho offline:** o formulário de registro salva em IndexedDB e envia quando a conexão volta. Usar uma chave de idempotência (`Idempotency-Key`) para não duplicar o registro se o reenvio acontecer duas vezes.
- Captura de foto e geolocalização do aparelho para preencher a coordenada e anexar evidência.
- Opcional: o próprio celular como rastreador da viatura, usando a credencial de telemetria por viatura que já existe (`emitir_credencial_telemetria.py`).
- *Push notification* quando chega uma ordem de despacho.

**Riscos.** É o maior item da lista: sincronização, conflitos de versão (o campo `versao` já existe), segurança dos dados guardados no aparelho e testes em dispositivos reais. Recomenda-se fatiar: (a) layout móvel, (b) PWA instalável, (c) rascunho offline, (d) *push*.

---

### #22. Escalonamento horizontal (Redis para WS, limitadores e cache)
| Escopo | Custo | Impacto |
|---|:---:|:---:|
| RNF01 | 4 | 3 |

**Situação atual.** O `GerenciadorConexoes`, o `PublicadorEmMemoria` e o `LimitadorEmMemoria` vivem na memória do processo. Com duas réplicas da API, um operador conectado à réplica A não recebe a posição GPS recebida pela réplica B, e o *rate limit* fica dividido.

**Proposta.**
- Adapters `PublicadorEventosRedis` (*pub/sub*) e `LimitadorTentativasRedis`, que implementam as **mesmas portas**, e um adapter WebSocket que se inscreve no canal.
- Escolha do adapter pelo `Settings` (`EVENTOS_BACKEND=memoria|redis`), mantendo o modo em memória para os testes e a demonstração.
- Redis entra como serviço opcional no compose (#18).

**Observação.** É uma boa demonstração prática do LSP e do DIP (AGENTS.md §4): troca-se a tecnologia sem tocar em `domain/` nem em `application/`.

---

### #23. Ciclo de vida de dados pessoais (LGPD)
| Escopo | Custo | Impacto |
|---|:---:|:---:|
| RNF02 | 4 | 4 |

**Situação atual.** Já há boas bases: máscara de CPF nos logs, ocultação de dados na consulta pública e código de acompanhamento. Mas não há:
- registro de **quem visualizou** os dados de um envolvido (só de quem os alterou);
- **finalidade** declarada no acesso a dados sensíveis (vítima de violência doméstica em medida protetiva, por exemplo);
- política de **retenção** e pseudonimização de comunicações públicas rejeitadas ou excluídas.

**Proposta.**
- Auditoria de leitura para dados sensíveis (envolvidos, medidas protetivas), com o campo "motivo do acesso" obrigatório nos casos mais sensíveis. Separar essa auditoria da "leitura de rotina" (ver N4 da análise).
- Uma classificação de sigilo na ocorrência (`PUBLICO`, `RESTRITO`, `SIGILOSO`), que limita quem pode abrir o detalhe.
- Uma tarefa de retenção que **pseudonimiza** (não apaga, por causa do RNF03) os dados pessoais de comunicações públicas `REJEITADA`/`EXCLUIDA` após o prazo definido pela equipe.
- Um relatório "acessos aos meus dados" para atender o direito do titular.

**Riscos.** Exige decisão jurídica e de produto sobre prazos e bases legais. Precisa conciliar o RNF03 (imutabilidade) com a LGPD (minimização), por isso pseudonimização em vez de exclusão.

---

### #24. Autenticação forte (MFA / SSO institucional)
| Escopo | Custo | Impacto |
|---|:---:|:---:|
| RNF02 | 4 | 3 |

**Proposta.**
- **MFA com TOTP** (aplicativo autenticador) obrigatório para DELEGADO e SUPERVISOR, que fazem atos irreversíveis (validar, arquivar, excluir) e geram o `hash_narrativa`.
- **SSO via OpenID Connect** (por exemplo, o provedor de identidade da secretaria de segurança), como um adapter a mais da porta de autenticação, mantendo o login local para a demonstração.
- **Reautenticação para atos críticos:** pedir a senha ou o TOTP de novo ao validar ou excluir uma ocorrência (*step-up*).

**Dependências.** #6 e #10.

---

## 5. Roteiro sugerido

| Fase | Itens | Justificativa |
|---|---|---|
| **Sprint A: ganhos rápidos do MVP** | ~~#1~~ ✅, ~~#2~~ ✅, #5, #4 | Pouco custo e melhora visível no uso diário de RF01, RF02 e RF04 |
| **Sprint B: fechar lacunas documentadas** | ~~#7~~ ✅, #9, #8 | #9 implementa um RNF04 que está documentado mas não existe; #7 e #8 fortalecem o RF04 |
| **Sprint C: segurança de contas** | #6, #10, ~~#13~~ ✅ (sem a troca obrigatória de senha, que depende do #6) | Nessa ordem, por dependência |
| **Sprint D: operação e entrega** | ~~#11~~ ✅, ~~#12~~ ✅, ~~#3~~ ✅, #18, #17 | Indicadores para a banca e um ambiente reproduzível |
| **Sprint E: integridade e robustez** | #16, #20 | Base para os jobs periódicos e para a entrega garantida de eventos |
| **Backlog: exige aprovação ou infraestrutura** | #14, #15, #19, #21, #22, #23, #24 | Ampliam extras, dependem de infraestrutura nova ou de decisão jurídica |

### 5.1 Antes de implementar qualquer item

1. Confirmar o escopo com a equipe (AGENTS.md §1.3), sobretudo para os itens marcados como **Extra**.
2. Atualizar `docs/DOCUMENTACAO_DE_ENGENHARIA.md` e os diagramas em `docs/diagramas/` (casos de uso, classes, sequência), que são a fonte única da verdade.
3. Respeitar a arquitetura hexagonal: as novas dependências (OSRM, Redis, bibliotecas de PDF/X.509, OpenTelemetry) entram **somente** em `adapters/` ou `infrastructure/` e são ligadas em `infrastructure/di.py`.
4. Nenhuma sugestão pede `DELETE` físico: desativação, pseudonimização e revogação são sempre lógicas (AGENTS.md §5).
5. Rodar as verificações obrigatórias (AGENTS.md §6): `lint-imports`, `pytest --cov` (≥ 80%), `tsc --noEmit` e `npm run build`.
