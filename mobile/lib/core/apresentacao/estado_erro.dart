import 'package:material_ui/material_ui.dart';

import 'contexto.dart';

/// Mensagem de erro centralizada com ação de nova tentativa.
class EstadoErro extends StatelessWidget {
  const EstadoErro({required this.mensagem, required this.aoTentarNovamente, super.key});

  final String mensagem;
  final VoidCallback aoTentarNovamente;

  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);
    final perigo = context.cores.perigo;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            DecoratedBox(
              decoration: BoxDecoration(
                color: perigo.withValues(alpha: 0.12),
                shape: BoxShape.circle,
              ),
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Icon(Icons.cloud_off_outlined, size: 40, color: perigo),
              ),
            ),
            const SizedBox(height: 16),
            Text(mensagem, textAlign: TextAlign.center, style: tema.textTheme.bodyLarge),
            const SizedBox(height: 20),
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
}
