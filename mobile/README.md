# 📱 SGOPI Sentinela — App Mobile (Flutter)

Cliente Android da mesma API REST `/v1` do backend. **Nenhuma alteração no backend** é necessária.

| Papel | O que faz no app | Requisito |
| :--- | :--- | :--- |
| **Agente** | Registra ocorrência com o GPS do aparelho, envolvidos, tipificações e fotos; acompanha as próprias; corrige e reenvia quando o Delegado devolve | RF01 / UC01 |
| **Delegado** | Fila de revisão (mais graves primeiro); valida, devolve ou rejeita com justificativa | RF04 / UC04 |
| Ambos | Abrem as fotos das evidências em tela cheia, com zoom (download autorizado, bloqueado se a integridade divergir; PDFs pelo web) | RF22 |
| Ambos | Aba **Notificações** com selo de não lidas (atualiza a cada 60 s); tocar abre a ocorrência citada | `/v1/notificacoes` |
| Ambos | Aba **Ajustes**: perfil, tema (sistema/claro/escuro), idioma (sistema/pt/en, vale também para as mensagens do backend), horário de expiração da sessão, servidor e versão | — |
| Outros papéis | Aviso para usar o sistema web | — |

Navegação: barra inferior com as abas do papel (Agente: Ocorrências · Notificações · Ajustes; Delegado: Fila · Notificações · Ajustes). Registrar, detalhar, corrigir e revisar abrem por cima, sem a barra, e o "voltar" retorna à aba de origem.

Visual: mesmas cores, fontes (Plus Jakarta Sans, Rajdhani, JetBrains Mono, embutidas em `assets/fontes/` com a licença OFL) e selos do frontend web, nos temas claro e escuro.

> **Limitação conhecida:** o título e a mensagem das notificações chegam do backend gravados em português; com o app em inglês, só eles ficam em português.

Próximo incremento: **RF02** (mapa em tempo real pelo WebSocket `/v1/tempo-real` e modo "terminal da viatura" com a credencial de dispositivo `X-Credencial-Dispositivo`).

---

## Arquitetura

Mesmas camadas do backend, por funcionalidade. As regras completas estão no [`AGENTS.md`](../AGENTS.md) §3 e são verificadas por [`test/arquitetura_test.dart`](test/arquitetura_test.dart).

```
lib/
├── core/
│   ├── dominio/       Falha, EnumApi, Pagina, Relogio (Dart puro)
│   ├── aplicacao/     PortaNaoConfigurada, relogioProvider
│   ├── http/          Dio (Bearer + Accept-Language + 401), Falha a partir do corpo {detail, code, request_id}
│   ├── apresentacao/  design/ (paleta do web, CoresSgopi, fontes), componentes/, rotas, mensagens de erro
│   └── l10n/          app_pt.arb, app_en.arb  (gerado/ sai do `flutter pub get`)
├── features/
│   ├── autenticacao/  login, sessão (8 h, sem refresh), papéis e permissões
│   ├── ocorrencias/   RF01: listar, detalhar, registrar, corrigir, reenviar, anexar evidência
│   ├── revisao/       RF04: fila e decisões do Delegado
│   ├── notificacoes/  lista, contador de não lidas, marcar como lida
│   └── preferencias/  tema e idioma (SharedPreferences) e a tela de Ajustes
│       └── domain/ · application/ · data/ · presentation/
└── app/
    ├── di.dart        COMPOSITION ROOT (único lugar que instancia adaptadores)
    ├── casca.dart     barra inferior (abas por papel + selo de notificações)
    ├── guarda_rotas.dart, roteador.dart, app.dart, tema.dart
```

| Camada | Pode importar | Exemplos |
| :--- | :--- | :--- |
| `domain/` | só `dart:*` e outros `domain/` | `DadosOcorrencia.validar`, `StatusOcorrencia.aceitaCorrecao`, portas `RepositorioOcorrencias` |
| `application/` | `domain/`, Dart puro, `package:riverpod` | `RegistrarOcorrencia.executar`, `ControladorSessao`, `ListaOcorrencias` |
| `data/` | `domain/`, Dio, plugins | `RepositorioOcorrenciasHttp`, `OcorrenciaMapper`, `LocalizacaoGeolocator` |
| `presentation/` | `application/`, `domain/`, `material_ui` | `TelaRegistrarOcorrencia`, `FormularioOcorrencia` |

---

## Ambiente de desenvolvimento (WSL2 + celular Android)

### 1. Flutter SDK no WSL

```bash
git clone --depth 1 -b stable https://github.com/flutter/flutter.git ~/flutter
echo 'export PATH="$HOME/flutter/bin:$PATH"' >> ~/.bashrc && source ~/.bashrc
flutter --disable-analytics
flutter --version          # testado com Flutter 3.50.1 / Dart 3.14
```

Só isso já basta para `flutter test` e `flutter analyze`.

### 2. Android SDK (para gerar e instalar o APK)

Precisa de um JDK 17+ (`java -version`).

```bash
mkdir -p ~/Android/Sdk/cmdline-tools && cd /tmp
# Pegue o nome atual em https://developer.android.com/studio#command-line-tools-only
curl -LO https://dl.google.com/android/repository/commandlinetools-linux-16111833_latest.zip
unzip commandlinetools-linux-*_latest.zip && mv cmdline-tools ~/Android/Sdk/cmdline-tools/latest
export ANDROID_HOME=~/Android/Sdk          # coloque também no ~/.bashrc
yes | ~/Android/Sdk/cmdline-tools/latest/bin/sdkmanager --licenses
~/Android/Sdk/cmdline-tools/latest/bin/sdkmanager "platform-tools" "platforms;android-36" "build-tools;36.0.0"
flutter config --android-sdk ~/Android/Sdk
flutter doctor                              # "Android toolchain" deve ficar ✓
```

### 3. Celular físico via depuração sem fio

1. No celular: **Opções do desenvolvedor → Depuração por Wi-Fi** (Android 11+), com PC e celular na mesma rede.
2. Toque em **Parear dispositivo com código** e, no WSL:

   ```bash
   export PATH="$ANDROID_HOME/platform-tools:$PATH"
   adb pair <IP-do-celular>:<porta-de-pareamento>   # digite o código mostrado
   adb connect <IP-do-celular>:<porta-de-conexão>   # a porta da tela principal da depuração sem fio
   flutter devices                                  # o aparelho deve aparecer
   ```

### 4. Backend acessível pelo celular

O celular precisa alcançar o backend que roda no WSL:

```bash
cd backend
uv run uvicorn --app-dir src main:app --host 0.0.0.0 --port 8000
```

- **Recomendado: rede espelhada do WSL.** Em `C:\Users\<voce>\.wslconfig`, adicione a seção `[wsl2]` com `networkingMode=mirrored` e rode `wsl --shutdown`. Assim o WSL usa o IP do Windows na rede local.
- **Alternativa (rede NAT padrão):** no PowerShell como administrador:

  ```powershell
  netsh interface portproxy add v4tov4 listenport=8000 listenaddress=0.0.0.0 connectport=8000 connectaddress=<IP-do-WSL>
  New-NetFirewallRule -DisplayName "SGOPI API" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
  ```

  O `<IP-do-WSL>` sai de `hostname -I` dentro do WSL.

- Use o IP do Windows na rede (`ipconfig`, adaptador Wi-Fi) como `API_BASE_URL`.

---

## Rodar

```bash
cd mobile
flutter pub get
flutter run --dart-define=API_BASE_URL=http://<IP-do-PC>:8000
```

- **Atalho com o celular conectado pelo adb (USB ou Wi-Fi):** `adb reverse tcp:8000 tcp:8000` e `--dart-define=API_BASE_URL=http://localhost:8000`. O `localhost:8000` do celular passa a apontar para o backend no WSL, sem mexer na rede do Windows. Só vale enquanto a depuração estiver ativa: refaça o `adb reverse` a cada novo `adb connect`.
- Sem `--dart-define`, o app usa `http://10.0.2.2:8000`, que é o endereço do PC visto do emulador Android.
- HTTP sem TLS só é liberado no build de **debug** (`android/app/src/debug/AndroidManifest.xml`). Release exige HTTPS.
- Usuários do seed (`uv run python -m scripts.seed`), todos com a senha `Senha@123`: `agente`, `delegado`.

Para gerar o APK e instalá-lo sem `flutter run`:

```bash
flutter build apk --debug --dart-define=API_BASE_URL=http://<IP-do-PC>:8000
adb install -r build/app/outputs/flutter-apk/app-debug.apk
```

---

## Testes e verificação

```bash
dart format lib test          # formatação (largura 100, em analysis_options.yaml)
flutter analyze               # lints + tipos estritos
flutter test                  # domínio, casos de uso, adaptadores HTTP, fluxos de tela e arquitetura
flutter test --coverage       # relatório em coverage/lcov.info
```

| Pasta | O que cobre |
| :--- | :--- |
| `test/arquitetura_test.dart` | contratos de dependência entre camadas (falha se, por exemplo, o `domain/` importar Dio) |
| `test/features/*/dominio_*` | regras espelhadas do backend (descrição ≥ 20, documento CPF/RG, limite de 10 evidências, justificativa ≥ 10) |
| `test/features/*/aplicacao_*`, `controlador_sessao_test.dart` | casos de uso e Notifiers com fakes (`test/fakes/`) |
| `test/features/*/dados_*`, `test/core/http_test.dart` | requisições e JSON exatamente como o backend espera, sem rede (`AdaptadorHttpFake`) |
| `test/app/` | guarda de rotas e abas por papel e fluxos completos (tela de celular 360×780 com texto 130%): login, registro, devolução, notificações, ajustes de tema/idioma e saída |
| `test/core/traducoes_test.dart` | `app_pt.arb` e `app_en.arb` com as mesmas chaves |

O `./scripts/verificar.sh` na raiz roda tudo isso (e o build do APK no modo completo) quando o Flutter está instalado. O CI roda o job `mobile-build`. Roteiro de TDD: skill [`mobile-tdd`](../.claude/skills/mobile-tdd/SKILL.md).
