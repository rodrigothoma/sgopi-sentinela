import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:material_ui/material_ui.dart';

import '../../../core/apresentacao/contexto.dart';
import '../../../core/apresentacao/mensagem_falha.dart';
import '../../../core/dominio/falha.dart';
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
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 420),
              child: Form(key: _formulario, child: _campos(context, aviso)),
            ),
          ),
        ),
      ),
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
        Icon(Icons.shield_outlined, size: 64, color: tema.colorScheme.primary),
        const SizedBox(height: 8),
        Text(textos.appTitulo, textAlign: TextAlign.center, style: tema.textTheme.headlineSmall),
        Text(textos.loginSubtitulo, textAlign: TextAlign.center, style: tema.textTheme.bodyMedium),
        const SizedBox(height: 32),
        TextFormField(
          key: const Key('login.usuario'),
          controller: _login,
          decoration: InputDecoration(labelText: textos.loginCampoUsuario),
          autofillHints: const [AutofillHints.username],
          textInputAction: TextInputAction.next,
          validator: obrigatorio,
        ),
        const SizedBox(height: 16),
        TextFormField(
          key: const Key('login.senha'),
          controller: _senha,
          decoration: InputDecoration(labelText: textos.loginCampoSenha),
          obscureText: true,
          autofillHints: const [AutofillHints.password],
          onFieldSubmitted: (_) => _entrar(),
          validator: obrigatorio,
        ),
        if (aviso != null) ...[
          const SizedBox(height: 16),
          Text(
            aviso,
            key: const Key('login.aviso'),
            style: TextStyle(color: tema.colorScheme.error),
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
