import 'package:material_ui/material_ui.dart';

import '../../../../core/apresentacao/contexto.dart';
import '../../domain/enums.dart';
import '../rotulos.dart';

/// Marcador ▲▲ / ▲ / ■ / ▼ com o rótulo da prioridade.
class SeloPrioridade extends StatelessWidget {
  const SeloPrioridade(this.prioridade, {super.key});

  final PrioridadeOcorrencia prioridade;

  @override
  Widget build(BuildContext context) {
    final cor = prioridade.cor(context.cores);
    final estilo = Theme.of(context).textTheme.labelMedium?.copyWith(color: cor);
    return Text.rich(
      TextSpan(
        children: [
          TextSpan(text: '${prioridade.simbolo} ', style: estilo?.copyWith(fontSize: 11)),
          TextSpan(text: prioridade.rotulo(context.textos)),
        ],
      ),
      style: estilo?.copyWith(fontWeight: FontWeight.w600),
    );
  }
}
