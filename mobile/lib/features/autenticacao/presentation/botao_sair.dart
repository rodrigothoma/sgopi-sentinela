import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:material_ui/material_ui.dart';

import '../../../core/apresentacao/contexto.dart';
import '../application/controlador_sessao.dart';

/// Ação da AppBar com o nome do usuário e a saída da sessão.
class BotaoSair extends ConsumerWidget {
  const BotaoSair({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final usuario = ref.watch(sessaoAtualProvider)?.usuario;
    return PopupMenuButton<void>(
      icon: const Icon(Icons.account_circle_outlined),
      itemBuilder: (context) => [
        if (usuario != null)
          PopupMenuItem<void>(enabled: false, child: Text(context.textos.saudacao(usuario.nome))),
        PopupMenuItem<void>(
          onTap: () => ref.read(controladorSessaoProvider.notifier).sair(),
          child: ListTile(
            leading: const Icon(Icons.logout),
            title: Text(context.textos.sair),
            contentPadding: EdgeInsets.zero,
          ),
        ),
      ],
    );
  }
}
