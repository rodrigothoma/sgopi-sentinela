# Resumo das contribuições — semana de refatoração (nov/2026)

Resumo curto do que foi entregue na branch `fade` e enviado para a `dev`. O detalhamento item a item, com os commits, está em [`implementacao/PLANO_REFATORACAO_2026-11.md`](implementacao/PLANO_REFATORACAO_2026-11.md). O relatório da apresentação está em [`RELATORIO_REFATORACAO_2026-11.md`](RELATORIO_REFATORACAO_2026-11.md).

---

## Parte 1 — Refatoração da auditoria (minha entrega principal)

### Problema

A primeira versão do catálogo de auditoria (`domain/auditoria/catalogo.py`) era formada por dois enums de nomes, `OperacaoAuditada` e `EntidadeAuditada`. Na apresentação, o professor considerou esse formato fora do padrão: auditoria é uma parte dinâmica e deveria ser modelada com classes. Além disso, cada um dos 38 pontos que gravavam auditoria montava o `RegistroAuditoria` à mão e repetia o mesmo payload. O bloco `{status, versao}`, por exemplo, aparecia em 4 lugares, e 7 pontos não gravavam o IP.

### Solução: eventos de auditoria tipados

- **Classe base `EventoAuditoria`** (`domain/auditoria/evento.py`) com o padrão **Template Method**. O método `para_registro(contexto)` é o único que monta o registro; cada subclasse preenche só os passos: `id_entidade()`, `dados_antes()` e `dados_depois()`.
- **Uma classe por ação**, no `auditoria.py` de cada agregado. São 48 classes, como `OcorrenciaValidada`, `MedidaRevogada` e `ViaturaCadastrada`. Classes intermediárias abstratas eliminam a duplicação: `MudancaStatusOcorrencia` monta `{status, versao}` uma única vez.
- **Registro automático**: ao ser declarada, a subclasse entra sozinha no catálogo, sem lista mantida à mão. Na importação, a base valida o formato `dominio.acao`, recusa nomes duplicados e exige `ENTIDADE`.
- **`ContextoAuditoria`** guarda quem fez a ação, quando e de qual IP, separado do que aconteceu. Esse contexto é montado por `ator.contexto_auditoria(agora)`, então nenhum ponto esquece o IP.
- **Compatibilidade**: os payloads gravados continuam idênticos. Os registros antigos, que a tabela append-only não permite reescrever, são encontrados pelas `GRAFIAS_LEGADAS`.

Para criar uma ação auditável nova, basta declarar uma subclasse com `OPERACAO` e `ENTIDADE` e chamar:

```python
await self._auditoria.registrar(OcorrenciaValidada.de(...), ator.contexto_auditoria(agora))
```

### Trilha de auditoria (tela)

- **Catálogo dinâmico**: o endpoint `GET /v1/auditoria/catalogo` é gerado das classes. Os filtros de operação e entidade da tela vêm desse endpoint, no lugar da lista fixa de 24 + 6 que existia antes, e as 48 operações e 16 entidades têm rótulos em pt e en.
- **Paginação no servidor**: a tela mostra 50 registros por página, com resposta `{itens, total, limit, offset}`.
- **Filtro de período De/Até**, no fuso da operação (America/Sao_Paulo), também aplicado na exportação.
- **Componente comum `Paginacao`**: páginas numeradas com reticências, botões anterior e próxima, e o campo "Ir para" para escolher a página direto.
- **Seed** atualizado para gravar os eventos novos.
- **Testes**: unitários da base e de cada família de eventos, teste do endpoint, Vitest da lógica de paginação e Cypress da trilha.

---

## Parte 2 — Demais ajustes da semana

### Bugs e segurança (Onda 0)

- **Sigilo de ofícios**: a consulta ignorava o ator e o sigilo vazava por notificações e pelo WebSocket. Além disso, o frontend enviava `RESTRITO`, valor que não existe no backend, então todo ofício "Restrito" era gravado como público.
- **Data em UTC nas medidas protetivas**: entre 21h e 24h o sistema adiantava o dia.
- **Ofícios**: a listagem perdia registros, porque o filtro era aplicado depois do `LIMIT`, e havia corrida na numeração, corrigida com UPSERT.
- **Permissão de inquéritos**: frontend, router e caso de uso aplicavam regras diferentes; agora há uma regra única.
- **Fakes de teste fora do contrato**: o mesmo conjunto de testes passou a rodar contra o fake e contra o SQL.
- **CI**: dependência com alerta de severidade alta corrigida (`npm audit`).

### Fundações de domínio (Onda 1)

- **Permissões centralizadas** em `domain/usuario/permissoes.py`: uma tabela ligando cada permissão aos papéis autorizados, usada por `ator.exigir(...)` e `exigir_permissao(...)`.
- **Máquina de estados genérica**: Ocorrência, Viatura, Inquérito e Medida declaram suas transições numa tabela.
- **Mixin `Versionado`**: `_tocar(instante)` controla a versão otimista das 5 entidades versionadas.
- **Helpers de validação e enums**: `exigir_texto`, `interpretar_enum`, escala única de `Prioridade` e prazos com nome.
- **Hash da narrativa** extraído da `Ocorrencia`, com uma estratégia por versão.

### Ferramentas e documentação

- **Pre-commit versionado** (ruff, import-linter, tsc e checagem de artefatos de IA) e `scripts/verificar.sh`, que repete o CI localmente.
- **Skills de agente**: `backend-tdd`, `frontend-tdd`, `verificar` e `handoff`. O `CLAUDE.md` importa o `AGENTS.md`.
- **Documentação** alinhada com o código: AGENTS.md, README, plano e relatório.

---

## Parte 3 — Paginação: o que ficou bom e o que fica para depois

**Ficou bom: trilha de auditoria.** A paginação é feita no servidor, com páginas numeradas e o campo "Ir para", e combina bem com uma tabela grande.

**Ficou estranho: listas de seleção dentro dos modais.** Nos modais de Laudos ("Solicitar laudo") e de Medidas Protetivas ("Conceder medida"), o seletor de ocorrência é um `GlideSelect` com 10 itens por página, e os botões de página ficam fora da lista. Para ver a próxima página, a pessoa precisa fechar a lista, avançar e abrir de novo. O vínculo de ocorrências do Inquérito tem paginação própria, que também é diferente das outras. Além disso, as três telas carregam só as 100 primeiras ocorrências e paginam no navegador.

**Refatoração futura (registrada na Onda 4 do plano):** criar um componente próprio para escolher registros em modais, o `SeletorOcorrencia`, com:

- **campo de busca** (protocolo, tipo, endereço) consultando o servidor, em vez de limitar às 100 primeiras;
- **lista que carrega mais itens ao rolar** ("carregar mais" ou rolagem infinita), sem fechar a lista para trocar de página;
- **um único componente** reutilizado em Laudos, Medidas Protetivas e Inquéritos, substituindo as três implementações atuais.

A paginação numerada (`Paginacao`) continua sendo a opção para tabelas de página inteira, como a trilha de auditoria.
