import 'package:material_ui/material_ui.dart';

import '../../../../core/apresentacao/contexto.dart';
import '../../domain/enums.dart';
import '../rotulos.dart';

/// Selo colorido do status: pendências do usuário em destaque, finais em neutro.
class SeloStatus extends StatelessWidget {
  const SeloStatus(this.status, {super.key});

  final StatusOcorrencia status;

  @override
  Widget build(BuildContext context) {
    final cores = Theme.of(context).colorScheme;
    final (fundo, texto) = switch (status) {
      StatusOcorrencia.aguardandoRevisao => (cores.tertiaryContainer, cores.onTertiaryContainer),
      StatusOcorrencia.emCorrecao ||
      StatusOcorrencia.rejeitada => (cores.errorContainer, cores.onErrorContainer),
      StatusOcorrencia.validada ||
      StatusOcorrencia.emAtendimento => (cores.primaryContainer, cores.onPrimaryContainer),
      _ => (cores.surfaceContainerHighest, cores.onSurfaceVariant),
    };
    return DecoratedBox(
      decoration: BoxDecoration(color: fundo, borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
        child: Text(
          status.rotulo(context.textos),
          style: Theme.of(context).textTheme.labelMedium?.copyWith(color: texto),
        ),
      ),
    );
  }
}
