import 'package:material_ui/material_ui.dart';

/// Cartão com título que agrupa um bloco do detalhe ou do formulário.
class CartaoSecao extends StatelessWidget {
  const CartaoSecao({required this.titulo, required this.filhos, this.icone, this.acao, super.key});

  final String titulo;
  final IconData? icone;
  final Widget? acao;
  final List<Widget> filhos;

  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);
    return Card(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                if (icone != null) ...[
                  Icon(icone, size: 20, color: tema.colorScheme.primary),
                  const SizedBox(width: 8),
                ],
                Expanded(child: Text(titulo, style: tema.textTheme.titleMedium)),
                ?acao,
              ],
            ),
            const SizedBox(height: 8),
            ...filhos,
          ],
        ),
      ),
    );
  }
}
