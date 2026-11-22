import 'package:material_ui/material_ui.dart';

import '../../../../core/apresentacao/contexto.dart';
import '../../domain/enums.dart';
import '../../domain/ocorrencia.dart';
import '../rotulos.dart';
import 'selo_status.dart';

class CartaoOcorrencia extends StatelessWidget {
  const CartaoOcorrencia(this.ocorrencia, {required this.aoTocar, super.key});

  final OcorrenciaResumo ocorrencia;
  final VoidCallback aoTocar;

  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);
    final urgente = ocorrencia.prioridade == PrioridadeOcorrencia.urgente;
    return Card(
      child: InkWell(
        onTap: aoTocar,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(ocorrencia.numeroProtocolo, style: tema.textTheme.labelLarge),
                  ),
                  SeloStatus(ocorrencia.status),
                ],
              ),
              const SizedBox(height: 6),
              Text(ocorrencia.natureza, style: tema.textTheme.titleMedium),
              Text(ocorrencia.localizacao, maxLines: 1, overflow: TextOverflow.ellipsis),
              const SizedBox(height: 6),
              Row(
                children: [
                  Icon(
                    Icons.flag_outlined,
                    size: 16,
                    color: urgente ? tema.colorScheme.error : null,
                  ),
                  const SizedBox(width: 4),
                  Text(ocorrencia.prioridade.rotulo(context.textos)),
                  const Spacer(),
                  Text(context.dataHora(ocorrencia.dataHoraFato), style: tema.textTheme.bodySmall),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
