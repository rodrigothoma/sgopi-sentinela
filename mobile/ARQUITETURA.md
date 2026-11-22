# 🧭 Guia da estrutura do `mobile/`

Mapa para entender o app sem conhecer Flutter a fundo. Como rodar e testar está no [`README.md`](README.md); as regras obrigatórias, no [`AGENTS.md`](../AGENTS.md) §3.

---

## 1. As peças em 1 minuto

| Peça | O que é | Equivalente que você já conhece |
| :--- | :--- | :--- |
| **Dart** | A linguagem, tipada, parecida com TypeScript/Java | Python do backend, TS do frontend |
| **Flutter** | Framework de interface: tudo na tela é um *widget* (classe com `build()` que devolve outros widgets) | Componentes React |
| **`material_ui`** | Biblioteca de componentes visuais (botões, cartões, barra de abas) | CSS + componentes do web |
| **Riverpod** | Guarda o estado e faz a injeção de dependências por *providers* | `Depends()` do FastAPI + hooks do React |
| **go_router** | Navegação entre telas por caminhos (`/ocorrencias/123`) | React Router |
| **Dio** | Cliente HTTP | `axios` do frontend |
| **ARB** (`app_pt.arb`, `app_en.arb`) | Arquivos de tradução; o Flutter gera a classe `Textos` a partir deles | `locales/*.json` do i18next |

---

## 2. A ideia central: o mesmo hexágono do backend

Cada funcionalidade (*feature*) tem quatro camadas, e as dependências só apontam para dentro:

```text
presentation  ──►  application  ──►  domain  ◄──  data
  (telas)         (casos de uso)    (regras +      (HTTP, GPS,
                                     portas)        câmera, disco)
```

| Camada | Pode usar | Não pode usar | No backend seria |
| :--- | :--- | :--- | :--- |
| `domain/` | só Dart puro | Flutter, Dio, Riverpod, plugins | `src/domain/` |
| `application/` | `domain/` e Riverpod puro | Flutter, Dio, `data/` | `src/application/use_cases/` |
| `data/` | `domain/`, Dio, plugins | telas | `src/adapters/outbound/` |
| `presentation/` | `application/`, `domain/`, `material_ui` | `data/`, Dio | `src/adapters/inbound/http/` |

As **portas** são interfaces em `domain/portas.dart` (por exemplo, `RepositorioOcorrencias`). O caso de uso só conhece a porta. Quem decide que ela é atendida por HTTP é o **composition root**, [`lib/app/di.dart`](lib/app/di.dart), no papel do `infrastructure/di.py`.

O teste [`test/arquitetura_test.dart`](test/arquitetura_test.dart) lê os `import` de todos os arquivos e falha se uma camada usar o que não pode. Ele faz o papel do import-linter.

---

## 3. Mapa das pastas

```text
mobile/
├── pubspec.yaml            dependências e versão do app (como o pyproject.toml / package.json)
├── pubspec.lock            versões exatas instaladas (vai para o git)
├── analysis_options.yaml   regras do analisador (lint), largura de linha 100
├── l10n.yaml               configuração da geração de traduções
├── assets/
│   ├── logo.svg            distintivo do SGOPI (derivado de frontend/public/logo.svg)
│   └── fontes/             Plus Jakarta Sans, Rajdhani, JetBrains Mono + licenças OFL
├── android/                projeto nativo Android (permissões, ícone, nome do app)
├── lib/                    código do app ↓
└── test/                   testes ↓
```

### `lib/main.dart`
Ponto de entrada. Carrega os formatos de data, registra as licenças das fontes, monta os adaptadores (`di.dart`) e abre o `AppSgopi`.

### `lib/app/`: montagem do app (o único lugar que conhece tudo)

| Arquivo | Função |
| :--- | :--- |
| `di.dart` | **Composition root**: liga cada porta ao adaptador real (HTTP, GPS, câmera, armazenamento) e cria o cliente HTTP com token e idioma |
| `app.dart` | `MaterialApp`: temas claro/escuro, idioma escolhido e o roteador |
| `tema.dart` | Tema visual: cores, fontes e estilo de cada componente |
| `roteador.dart` | Todas as rotas. As abas ficam num `StatefulShellRoute`; as telas de fluxo abrem por cima |
| `casca.dart` | Barra inferior com as abas do papel e o selo de notificações |
| `guarda_rotas.dart` | Quem pode ver o quê: abas por papel e redirecionamento (sem login → login) |

### `lib/core/`: compartilhado por todas as features

| Pasta / arquivo | Função |
| :--- | :--- |
| `dominio/falha.dart` | `Falha`: o erro do app (sem conexão, 401, 409, 422...) com `detail`, `code` e `request_id` do backend |
| `dominio/enum_api.dart` | Enums com o código exato do backend (`AGUARDANDO_REVISAO`...) |
| `dominio/pagina.dart`, `relogio.dart` | Página de resultados; relógio injetável (os testes usam um fixo) |
| `aplicacao/dependencias.dart` | `PortaNaoConfigurada` (porta sem adaptador), relógio e versão do app |
| `config/ambiente.dart` | `API_BASE_URL` vinda do `--dart-define` |
| `http/cliente_http.dart` | Cria o Dio: Bearer, `Accept-Language` e "401 encerra a sessão" |
| `http/falhas_http.dart` | Converte o erro HTTP em `Falha` lendo `{detail, code, request_id}` |
| `http/json.dart` | Leitura tipada de JSON (campo faltando = erro claro) |
| `apresentacao/design/` | `paleta.dart` (cores do web), `cores_sgopi.dart` (cores semânticas no tema), `tipografia.dart` (fontes) |
| `apresentacao/componentes/` | Blocos visuais reutilizados: `CartaoSecao`, `EstadoVazio`, `ListaCarregando`, `BarraAcoes`, `AvatarIniciais`, `LinhaInfo`, `LogoSgopi` |
| `apresentacao/contexto.dart` | Atalhos: `context.textos`, `context.cores`, `context.dataHora`, `context.avisar` |
| `apresentacao/rotas.dart` | Caminhos das telas num só lugar |
| `apresentacao/mensagem_falha.dart`, `estado_erro.dart` | Texto e tela de erro ("... (ref. abcd1234)" + Tentar novamente) |
| `l10n/app_pt.arb`, `app_en.arb` | Traduções; `l10n/gerado/` sai do `flutter pub get` e não vai para o git |

### `lib/features/`: uma pasta por funcionalidade

**`autenticacao/`**: login e sessão
- `domain/`: `Usuario`, `Papel` (AGENTE, DELEGADO...), `Permissao` (quem registra, quem revisa), `Sessao` (expira em 8 h) e as portas.
- `application/controlador_sessao.dart`: entra, sai, restaura a sessão salva ao abrir o app e expira no 401.
- `data/`: login HTTP, `SessaoMapper` (JSON ↔ entidade) e o token no armazenamento seguro do Android.
- `presentation/`: tela de login, tela "use o sistema web" e os rótulos dos papéis.

**`ocorrencias/`**: RF01, o Agente em campo
- `domain/`:
  - `ocorrencia.dart`: entidades (resumo, detalhe, envolvido, evidência, histórico);
  - `dados_ocorrencia.dart`: validações espelhadas do backend (descrição ≥ 20, CPF/RG...);
  - `arquivo_evidencia.dart`: JPG/PNG/PDF, até 10 MB e 10 arquivos;
  - `enums.dart`: status, prioridade e tipo de envolvido;
  - `portas.dart`: repositório, GPS e câmera.
- `application/`:
  - casos de uso: `registrar_ocorrencia.dart` (valida → cria → envia as fotos), `corrigir_ocorrencia.dart`;
  - estado das telas: `lista_ocorrencias.dart` (paginação), `detalhe_ocorrencia.dart`, `conteudo_evidencia.dart` (download da foto).
- `data/`: repositório HTTP, `OcorrenciaMapper`, GPS (`geolocator`) e câmera (`image_picker`).
- `presentation/`:
  - telas: minhas ocorrências, registrar, detalhe, corrigir e visualizar foto;
  - `widgets/`: cartão, selos, formulário, diálogos, painel de fotos, lista paginada.

**`revisao/`**: RF04, o Delegado
- `domain/decisao_revisao.dart`: Validar, Devolver ou Rejeitar; justificativa ≥ 10 nas duas últimas.
- `application/`: `decidir_revisao.dart` (valida e envia) e `fila_revisao.dart` (filtro: aguardando revisão, por prioridade).
- `data/`: `repositorio_revisao_http.dart` escolhe `/validar`, `/devolver` ou `/rejeitar`.
- `presentation/`: fila, tela de revisão (reaproveita o detalhe de ocorrências) e o diálogo da decisão.

**`notificacoes/`**: avisos do backend
- `domain/`: `Notificacao`, que lê o id da ocorrência no `link`.
- `application/`: lista paginada com "marcar como lida" otimista e o contador de não lidas (atualiza a cada 60 s).
- `data/`: `/v1/notificacoes` e o mapper.
- `presentation/`: aba de Notificações.

**`preferencias/`**: tema e idioma
- `domain/`: `ModoTema` (sistema/claro/escuro), `IdiomaApp` (sistema/pt/en) e a porta.
- `application/`: controlador que aplica e salva; idioma efetivo para o `Accept-Language`.
- `data/`: `SharedPreferences`, com as mesmas chaves do localStorage do web.
- `presentation/`: aba de Ajustes e os atalhos de tema/idioma do login.

---

## 4. Uma ação de ponta a ponta: o Delegado valida uma ocorrência

```text
TelaRevisarOcorrencia (botão Validar)                   presentation
  └─ abrirDialogoDecisao()  → Validar(despacho)         presentation
      └─ DecidirRevisao.executar(id, decisao)           application
          ├─ decisao.validar()                          domain
          └─ RepositorioRevisao.decidir(...)            domain (porta)
              └─ RepositorioRevisaoHttp                 data (ligado em app/di.dart)
                  └─ Dio POST /v1/ocorrencias/{id}/validar   + Bearer + Accept-Language
                      └─ backend responde o detalhe atualizado
                  ◄─ OcorrenciaMapper.detalheDeJson()   data
  ◄─ detalheOcorrenciaProvider.atualizarCom(...)        application (estado)
  ◄─ a fila é recarregada, aparece o aviso, volta para a fila   presentation
```

Se o backend recusar, `falhas_http.dart` transforma a resposta em `Falha` e a tela mostra `mensagemDeFalha`, com a mensagem traduzida e a referência da requisição.

---

## 5. "Quero mudar X, onde mexo?"

| Quero... | Arquivo |
| :--- | :--- |
| Mudar uma cor ou fonte | `core/apresentacao/design/paleta.dart` / `app/tema.dart` |
| Mudar um texto (ou traduzir) | `core/l10n/app_pt.arb` **e** `app_en.arb` |
| Adicionar uma tela | `features/<f>/presentation/` + rota em `core/apresentacao/rotas.dart` e `app/roteador.dart` |
| Mudar quem vê qual aba | `app/guarda_rotas.dart` (`abasDoPapel`) |
| Mudar uma regra (ex.: tamanho mínimo) | `features/<f>/domain/`, conferindo a mesma regra no backend |
| Chamar um endpoint novo | método na porta (`domain/portas.dart`) → implementação em `data/` → uso em `application/` |
| Trocar um adaptador (ex.: outro plugin de câmera) | só `data/` + a ligação em `app/di.dart` |

---

## 6. Testes (`test/`)

| Pasta | O que garante |
| :--- | :--- |
| `fakes/` | Versões falsas das portas (sem rede, sem GPS) e um `AdaptadorHttpFake` que imita o backend; `container.dart` faz o papel do `di.dart` nos testes |
| `features/*/dominio_*` | Regras puras (validações, status, decisões) |
| `features/*/aplicacao_*`, `controlador_sessao_test`, `notificacoes_test`, `preferencias_test` | Casos de uso e estados com os fakes |
| `features/*/dados_*`, `core/http_test` | JSON e rotas exatamente como o backend espera |
| `app/guarda_rotas_test` | Quem acessa cada tela e aba |
| `app/fluxos_test` | O app inteiro, numa tela de celular com texto a 130%: login, registro, revisão, fotos, notificações, ajustes, sair |
| `core/traducoes_test` | Toda chave em português existe em inglês |
| `arquitetura_test` | Nenhuma camada importa o que não pode |

```bash
flutter test                       # tudo
flutter test test/app/fluxos_test.dart --plain-name "Delegado"   # só um teste
```
