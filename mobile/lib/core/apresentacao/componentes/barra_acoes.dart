import 'package:material_ui/material_ui.dart';

import '../contexto.dart';

/// Rodapé fixo com as ações da tela, separado do conteúdo por uma linha.
class BarraAcoes extends StatelessWidget {
  const BarraAcoes({required this.child, super.key});

  final Widget child;

  @override
  Widget build(BuildContext context) => DecoratedBox(
    decoration: BoxDecoration(
      color: Theme.of(context).colorScheme.surface,
      border: Border(top: BorderSide(color: context.cores.linha)),
    ),
    child: SafeArea(
      top: false,
      child: Padding(padding: const EdgeInsets.fromLTRB(16, 12, 16, 12), child: child),
    ),
  );
}
