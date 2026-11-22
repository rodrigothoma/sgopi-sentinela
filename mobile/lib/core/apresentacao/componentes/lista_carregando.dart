import 'package:material_ui/material_ui.dart';

/// Cartões-esqueleto pulsando enquanto a primeira página carrega.
class ListaCarregando extends StatefulWidget {
  const ListaCarregando({this.quantidade = 5, super.key});

  final int quantidade;

  @override
  State<ListaCarregando> createState() => _ListaCarregandoState();
}

class _ListaCarregandoState extends State<ListaCarregando> with SingleTickerProviderStateMixin {
  late final _pulso = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 900),
    lowerBound: 0.4,
  )..repeat(reverse: true);

  @override
  void dispose() {
    _pulso.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final cor = Theme.of(context).colorScheme.surfaceContainerHighest;
    Widget barra(double largura, double altura) => FractionallySizedBox(
      alignment: Alignment.centerLeft,
      widthFactor: largura,
      child: Container(
        height: altura,
        decoration: BoxDecoration(color: cor, borderRadius: BorderRadius.circular(6)),
      ),
    );
    return Semantics(
      label: MaterialLocalizations.of(context).refreshIndicatorSemanticLabel,
      child: FadeTransition(
        opacity: _pulso,
        child: ListView.separated(
          physics: const NeverScrollableScrollPhysics(),
          padding: const EdgeInsets.all(16),
          itemCount: widget.quantidade,
          separatorBuilder: (_, _) => const SizedBox(height: 12),
          itemBuilder: (_, _) => Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                spacing: 10,
                children: [barra(0.4, 12), barra(0.8, 18), barra(0.6, 12)],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
