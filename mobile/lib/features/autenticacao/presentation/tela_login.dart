import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:material_ui/material_ui.dart';

import '../../../core/apresentacao/componentes/logo_sgopi.dart';
import '../../../core/apresentacao/contexto.dart';
import '../../../core/apresentacao/mensagem_falha.dart';
import '../../../core/dominio/falha.dart';
import '../../preferencias/presentation/botoes_preferencias.dart';
import '../application/controlador_sessao.dart';

class TelaLogin extends ConsumerStatefulWidget {
  const TelaLogin({super.key});

  @override
  ConsumerState<TelaLogin> createState() => _TelaLoginState();
}

class _TelaLoginState extends ConsumerState<TelaLogin> {
  final _formulario = GlobalKey<FormState>();
  final _login = TextEditingController();
  final _senha = TextEditingController();
  bool _entrando = false;
  bool _senhaVisivel = false;
  String? _erro;

  @override
  void dispose() {
    _login.dispose();
    _senha.dispose();
    super.dispose();
  }

  Future<void> _entrar() async {
    if (!_formulario.currentState!.validate()) return;
    setState(() {
      _entrando = true;
      _erro = null;
    });
    try {
      await ref
          .read(controladorSessaoProvider.notifier)
          .entrar(login: _login.text, senha: _senha.text);
    } on Falha catch (falha) {
      if (mounted) setState(() => _erro = mensagemDeFalha(context.textos, falha));
    } finally {
      if (mounted) setState(() => _entrando = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final textos = context.textos;
    final estado = ref.watch(controladorSessaoProvider).value;
    final aviso = _erro ?? (estado is SemSessao && estado.expirou ? textos.sessaoExpirada : null);
    return Scaffold(
      body: SafeArea(
        child: Stack(
          children: [
            Center(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(24, 56, 24, 24),
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 420),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      _marca(context),
                      const SizedBox(height: 32),
                      Card(
                        child: Padding(
                          padding: const EdgeInsets.all(20),
                          child: Form(key: _formulario, child: _campos(context, aviso)),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
            const Positioned(top: 4, right: 4, child: BotoesPreferencias()),
          ],
        ),
      ),
    );
  }

  Widget _marca(BuildContext context) {
    final textos = context.textos;
    final tema = Theme.of(context);
    return Column(
      children: [
        const LogoSgopi(tamanho: 88),
        const SizedBox(height: 12),
        Text(
          textos.appTitulo.toUpperCase(),
          textAlign: TextAlign.center,
          style: tema.textTheme.headlineMedium?.copyWith(letterSpacing: 2),
        ),
        Text(
          textos.loginSubtitulo,
          textAlign: TextAlign.center,
          style: tema.textTheme.bodyMedium?.copyWith(color: tema.colorScheme.onSurfaceVariant),
        ),
      ],
    );
  }

  Widget _campos(BuildContext context, String? aviso) {
    final textos = context.textos;
    final tema = Theme.of(context);
    String? obrigatorio(String? valor) =>
        (valor ?? '').trim().isEmpty ? textos.campoObrigatorio : null;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(textos.loginTitulo, style: tema.textTheme.titleLarge),
        const SizedBox(height: 16),
        TextFormField(
          key: const Key('login.usuario'),
          controller: _login,
          decoration: InputDecoration(
            labelText: textos.loginCampoUsuario,
            prefixIcon: const Icon(Icons.person_outline),
          ),
          autofillHints: const [AutofillHints.username],
          textInputAction: TextInputAction.next,
          validator: obrigatorio,
        ),
        const SizedBox(height: 16),
        TextFormField(
          key: const Key('login.senha'),
          controller: _senha,
          decoration: InputDecoration(
            labelText: textos.loginCampoSenha,
            prefixIcon: const Icon(Icons.lock_outline),
            suffixIcon: IconButton(
              tooltip: _senhaVisivel ? textos.ocultarSenha : textos.mostrarSenha,
              icon: Icon(_senhaVisivel ? Icons.visibility_off_outlined : Icons.visibility_outlined),
              onPressed: () => setState(() => _senhaVisivel = !_senhaVisivel),
            ),
          ),
          obscureText: !_senhaVisivel,
          autofillHints: const [AutofillHints.password],
          onFieldSubmitted: (_) => _entrar(),
          validator: obrigatorio,
        ),
        if (aviso != null) ...[
          const SizedBox(height: 16),
          DecoratedBox(
            decoration: BoxDecoration(
              color: tema.colorScheme.error.withValues(alpha: 0.10),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Row(
                children: [
                  Icon(Icons.error_outline, color: tema.colorScheme.error),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      aviso,
                      key: const Key('login.aviso'),
                      style: TextStyle(color: tema.colorScheme.error),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
        const SizedBox(height: 24),
        FilledButton(
          key: const Key('login.entrar'),
          onPressed: _entrando ? null : _entrar,
          child: _entrando
              ? const SizedBox.square(
                  dimension: 20,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : Text(textos.loginEntrar),
        ),
      ],
    );
  }
}
