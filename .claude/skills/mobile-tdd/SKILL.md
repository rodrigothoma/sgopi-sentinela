---
name: mobile-tdd
description: Roteiro de TDD para codificar no app mobile do SGOPI Sentinela (Flutter/Dart, Riverpod, Dio, go_router) — domínio, casos de uso, adaptadores HTTP, telas e i18n. Use ao implementar, alterar ou refatorar qualquer coisa em mobile/.
---

# Mobile com TDD

**Antes de tudo, leia o `AGENTS.md`** (stack, escopo, regras do `mobile/` e verificação). Esta skill é o *como* no app.

## Camadas e onde testar

| Camada | Pasta | Teste | Padrão a seguir |
| :--- | :--- | :--- | :--- |
| Domínio (Dart puro) | `lib/features/<f>/domain/`, `lib/core/dominio/` | unitário puro | `test/features/ocorrencias/dominio_ocorrencias_test.dart` |
| Aplicação (casos de uso, Notifiers) | `lib/features/<f>/application/` | `ProviderContainer` com fakes (`test/fakes/container.dart`) | `test/features/ocorrencias/aplicacao_ocorrencias_test.dart` |
| Adaptadores (HTTP, plugins) | `lib/features/<f>/data/`, `lib/core/http/` | Dio com `AdaptadorHttpFake` (sem rede) | `test/features/ocorrencias/dados_ocorrencias_test.dart` |
| Telas e fluxos | `lib/features/<f>/presentation/`, `lib/app/` | widget test do app inteiro sobre fakes | `test/app/fluxos_test.dart` |
| Arquitetura | `lib/**` | `test/arquitetura_test.dart` | não afrouxe: corrija o import |

- **Fakes escritos à mão** em `test/fakes/` (como `backend/tests/fakes`); sem mocktail. Fake novo de porta entra em `fakes.dart` e na classe `Dubles` de `container.dart`.
- JSON de exemplo no formato exato do backend (`test/fakes/exemplos.dart`, `detalheJson`): ao mudar um schema no backend, atualize o exemplo e o mapper no mesmo PR.
- Widget tests selecionam por `Key('tela.elemento')` (equivalente ao `data-cy` do Cypress); textos só para conferir mensagens.

## Ciclo

1. **Vermelho:** escreva o teste na camada certa e veja falhar pelo motivo certo: `flutter test test/caminho_test.dart`.
2. **Verde:** o mínimo de código para passar.
3. **Refatorar:** regra de negócio desce para o domínio; orquestração para um caso de uso com `executar(...)`; widget grande vira subwidget em `presentation/widgets/`.
4. Ao fim: `dart format lib test && flutter analyze && flutter test`; por último a skill `verificar`.

## Padrões do projeto

- **Portas e DI:** a porta é `abstract interface class` no `domain/`; o provider dela no `application/dependencias.dart` lança `PortaNaoConfigurada`; o adaptador concreto é ligado **só** em `lib/app/di.dart`.
- **Erros:** adaptadores trocam `DioException` por `Falha` com `comFalhasTraduzidas`; a tela mostra `mensagemDeFalha` (texto do backend + `ref.` do `request_id`). Validação local lança exceção de domínio (`DadosOcorrenciaInvalidos`, `EvidenciaInvalida`, `DecisaoInvalida`) antes de chamar a rede.
- **Valores enviados ao backend** são os códigos exatos dos enums do domínio (`EnumApi.codigo`); código desconhecido falha com `FormatException`, nunca cai num padrão silencioso.
- **Regras espelhadas** (tamanhos mínimos, limite de evidências, documento CPF/RG) ficam em constantes do domínio com o nome e o arquivo do backend no comentário. O backend continua sendo a autoridade.
- **Papéis:** `Permissao` em `features/autenticacao/domain/permissao.dart` espelha `backend/src/domain/usuario/permissoes.py`; a guarda de rotas (`app/guarda_rotas.dart`) só evita oferecer o que vai dar 403.
- **i18n:** todo texto visível vem de `context.textos`, com a chave em `lib/core/l10n/app_pt.arb` e `app_en.arb` (o código em `gerado/` sai do `flutter pub get`; não versionar).
- **Material:** importe `package:material_ui/material_ui.dart` (o `package:flutter/material.dart` está depreciado desde o Flutter 3.47).

## Pronto quando

- O comportamento novo tem teste que falhou antes do código, na camada certa; o fluxo de tela alterado tem widget test.
- Textos em pt e en, valores alinhados aos enums do backend, papéis alinhados ao catálogo de permissões.
- `dart format`, `flutter analyze` e `flutter test` verdes e `verificar` verde; commit no padrão Conventional Commits.
