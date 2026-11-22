import 'package:material_ui/material_ui.dart';

import '../../../core/apresentacao/contexto.dart';
import 'botao_sair.dart';

/// Papéis sem fluxo no app (Operador, Supervisor, Perito, Escrivão) usam o sistema web.
class TelaSemAcesso extends StatelessWidget {
  const TelaSemAcesso({super.key});

  @override
  Widget build(BuildContext context) {
    final textos = context.textos;
    return Scaffold(
      appBar: AppBar(title: Text(textos.appTitulo), actions: const [BotaoSair()]),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.desktop_windows_outlined, size: 56),
              const SizedBox(height: 12),
              Text(textos.semAcessoTitulo, style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 8),
              Text(textos.semAcessoMensagem, textAlign: TextAlign.center),
            ],
          ),
        ),
      ),
    );
  }
}
