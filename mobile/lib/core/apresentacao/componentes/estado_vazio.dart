import 'package:material_ui/material_ui.dart';

/// Ilustração por ícone para listas vazias, com ação opcional.
class EstadoVazio extends StatelessWidget {
  const EstadoVazio({
    required this.icone,
    required this.titulo,
    this.mensagem,
    this.acao,
    super.key,
  });

  final IconData icone;
  final String titulo;
  final String? mensagem;
  final Widget? acao;

  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);
    final cores = tema.colorScheme;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            DecoratedBox(
              decoration: BoxDecoration(
                color: cores.primary.withValues(alpha: 0.10),
                shape: BoxShape.circle,
              ),
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Icon(icone, size: 40, color: cores.primary),
              ),
            ),
            const SizedBox(height: 16),
            Text(titulo, style: tema.textTheme.titleMedium, textAlign: TextAlign.center),
            if (mensagem != null) ...[
              const SizedBox(height: 6),
              Text(
                mensagem!,
                textAlign: TextAlign.center,
                style: tema.textTheme.bodyMedium?.copyWith(color: cores.onSurfaceVariant),
              ),
            ],
            if (acao != null) ...[const SizedBox(height: 20), acao!],
          ],
        ),
      ),
    );
  }
}
