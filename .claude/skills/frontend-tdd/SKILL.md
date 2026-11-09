---
name: frontend-tdd
description: Roteiro de TDD para codificar no frontend do SGOPI Sentinela (React 18 + TypeScript + Vite, Vitest e Cypress) — páginas, componentes, hooks, serviços de API e i18n. Use ao implementar, alterar ou refatorar qualquer coisa em frontend/.
---

# Frontend com TDD

**Antes de tudo, leia o `AGENTS.md`** (stack, escopo e verificação). Esta skill é o *como* no frontend.

## Ferramentas de teste que existem (e as que não existem)

| Nível | Ferramenta | Onde | Quando |
| :--- | :--- | :--- | :--- |
| Lógica pura | Vitest (ambiente node) | `src/utils/__tests__/<modulo>.test.ts`, no padrão de `duracao.test.ts` e `filtrosOcorrencias.test.ts` | Formatação, filtros, regras de exibição, reducers de eventos, montagem de payloads |
| Fluxo de tela | Cypress | `cypress/e2e/<funcionalidade>.cy.ts` | Comportamento que depende de navegador, rotas, papéis ou da API real |

- **Não há Testing Library nem jsdom**: componente React não é testado isoladamente. Por isso, **tire a lógica do componente** (função pura em `src/utils/` ou lógica de hook em função pura) e teste-a no Vitest; deixe o componente fino. Adicionar `@testing-library/react` + `jsdom` é decisão do time (Onda 4 do plano): não instale por conta própria.
- **Cypress** precisa do backend em `:8000` com seed (`npm run e2e:db`) e do `npm run dev` em `:3000`. Comandos prontos em `cypress/support/commands.ts`: `cy.login(perfil, caminho)`, `cy.loginPelaTela(login, senha)`, `cy.apiComo(perfil, metodo, url, body)`, `cy.criarOcorrenciaApi(overrides)`. Selecione elementos por `data-cy="..."` (acrescente o atributo no componente), não por texto ou classe de estilo.

## Ciclo

1. **Vermelho:** escreva o teste (Vitest para a lógica; spec Cypress para o fluxo) e veja falhar pelo motivo certo: `npx vitest run src/utils/__tests__/<x>.test.ts`.
2. **Verde:** o mínimo de código para passar.
3. **Refatorar:** extraia hook (`src/hooks/useXxx`) para busca de dados e estado, subcomponente para modal/formulário, classe CSS no lugar de `style={{...}}`; rode de novo.
4. Ao fim: `npx tsc --noEmit && npm test && npm run build`; se mexeu em fluxo coberto pelo Cypress, `npm run e2e -- --spec cypress/e2e/<x>.cy.ts`; por último a skill `verificar`.

## Padrões do projeto

- **API:** toda chamada passa pela instância axios de `src/services/api.ts` (já trata token, 401 e mensagem de erro), num serviço por domínio em `src/services/`. Tipos de resposta em `src/types/api.ts`; ao tocar num serviço que declara tipos próprios, mova-os para lá. Sem `any`.
- **Valores enviados ao backend** são exatamente os valores dos enums do domínio (`backend/src/domain/**`). Confira antes de criar um `<select>`: a opção `RESTRITO`, inexistente no backend, gravou ofícios restritos como públicos.
- **Papéis na interface:** `RequireRole papeis={[...]}` em `src/App.tsx` e `tem(...)` no `Sidebar` espelham o catálogo `backend/src/domain/usuario/permissoes.py`. Esconder na tela não é segurança: a regra vale no backend; a tela só evita oferecer o que vai dar 403.
- **i18n:** todo texto visível via `t('namespace:chave')`, com a mesma chave em `src/locales/pt/` e `src/locales/en/`; namespace novo é registrado em `src/i18n.ts`. Erros da API trazem `code` (chave i18n do backend) e `detail`.
- **Tempo real:** use `useTempoReal`; não abra outro `ClienteTempoReal` nem faça polling do que já chega pelo WebSocket.
- **Componentes comuns:** reaproveite `src/components/common/` (ex.: `GlideSelect`) antes de criar outro; modal, seletor de ocorrência e formulários repetidos entre páginas viram componente comum.
- **Tamanho:** página que passa de ~300 linhas ou acumula muitos `useState` é sinal para extrair hook e subcomponentes (ver Onda 4 do plano).

## Pronto quando

- A lógica nova tem teste Vitest que falhou antes do código; o fluxo novo ou alterado tem spec Cypress (ou o existente foi atualizado).
- Textos em pt e en, valores alinhados aos enums do backend, papéis alinhados ao catálogo de permissões.
- `tsc`, Vitest e build verdes e `verificar` verde; commit no padrão Conventional Commits.
