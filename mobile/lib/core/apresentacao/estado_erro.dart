import 'package:material_ui/material_ui.dart';

import 'contexto.dart';

/// Mensagem de erro centralizada com ação de nova tentativa.
class EstadoErro extends StatelessWidget {
  const EstadoErro({required this.mensagem, required this.aoTentarNovamente, super.key});

  final String mensagem;
  final VoidCallback aoTentarNovamente;

  @override
  Widget build(BuildContext context) => Center(
    child: Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.cloud_off, size: 48, color: Theme.of(context).colorScheme.error),
          const SizedBox(height: 12),
          Text(mensagem, textAlign: TextAlign.center),
          const SizedBox(height: 16),
          OutlinedButton.icon(
            onPressed: aoTentarNovamente,
            icon: const Icon(Icons.refresh),
            label: Text(context.textos.tentarNovamente),
          ),
        ],
      ),
    ),
  );
}
