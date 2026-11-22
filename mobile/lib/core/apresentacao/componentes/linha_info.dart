import 'package:material_ui/material_ui.dart';

/// Ícone + rótulo pequeno + valor, para dados do detalhe e dos ajustes.
class LinhaInfo extends StatelessWidget {
  const LinhaInfo({
    required this.icone,
    required this.rotulo,
    required this.valor,
    this.estiloValor,
    super.key,
  });

  final IconData icone;
  final String rotulo;
  final String valor;
  final TextStyle? estiloValor;

  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icone, size: 20, color: tema.colorScheme.onSurfaceVariant),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  rotulo,
                  style: tema.textTheme.labelMedium?.copyWith(
                    color: tema.colorScheme.onSurfaceVariant,
                  ),
                ),
                const SizedBox(height: 2),
                SelectableText(valor, style: estiloValor ?? tema.textTheme.bodyMedium),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
