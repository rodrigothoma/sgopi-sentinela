import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:material_ui/material_ui.dart';

import '../../../core/apresentacao/componentes/estado_vazio.dart';
import '../../../core/apresentacao/contexto.dart';
import '../../preferencias/presentation/botoes_preferencias.dart';
import '../application/controlador_sessao.dart';

/// Papéis sem fluxo no app (Operador, Supervisor, Perito, Escrivão) usam o sistema web.
class TelaSemAcesso extends ConsumerWidget {
  const TelaSemAcesso({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final textos = context.textos;
    return Scaffold(
      appBar: AppBar(title: Text(textos.appTitulo), actions: const [BotoesPreferencias()]),
      body: EstadoVazio(
        icone: Icons.desktop_windows_outlined,
        titulo: textos.semAcessoTitulo,
        mensagem: textos.semAcessoMensagem,
        acao: OutlinedButton.icon(
          key: const Key('semAcesso.sair'),
          onPressed: () => ref.read(controladorSessaoProvider.notifier).sair(),
          icon: const Icon(Icons.logout),
          label: Text(textos.sair),
        ),
      ),
    );
  }
}
