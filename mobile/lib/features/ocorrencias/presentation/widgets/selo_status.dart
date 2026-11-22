import 'package:material_ui/material_ui.dart';

import '../../../../core/apresentacao/contexto.dart';
import '../../../../core/apresentacao/design/cores_sgopi.dart';
import '../../../../core/apresentacao/design/tipografia.dart';
import '../../domain/enums.dart';
import '../rotulos.dart';

/// Pílula do status com "●" e a cor do web, em Rajdhani maiúsculo.
class SeloStatus extends StatelessWidget {
  const SeloStatus(this.status, {super.key});

  final StatusOcorrencia status;

  @override
  Widget build(BuildContext context) {
    final cor = status.cor(context.cores);
    return DecoratedBox(
      decoration: BoxDecoration(
        color: CoresSgopi.fundoDe(cor),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
        child: Text(
          '● ${status.rotulo(context.textos).toUpperCase()}',
          style: TextStyle(
            fontFamily: Fontes.destaque,
            fontWeight: FontWeight.w700,
            fontSize: 13,
            letterSpacing: 0.4,
            color: cor,
            decoration: status == StatusOcorrencia.excluida ? TextDecoration.lineThrough : null,
          ),
        ),
      ),
    );
  }
}
