import 'package:material_ui/material_ui.dart';

import '../../../../core/apresentacao/contexto.dart';
import '../../../../core/apresentacao/design/tipografia.dart';
import '../../domain/ocorrencia.dart';
import '../rotulos.dart';
import 'selo_prioridade.dart';
import 'selo_status.dart';

/// Item das listas: faixa lateral na cor da prioridade, protocolo, natureza e local.
class CartaoOcorrencia extends StatelessWidget {
  const CartaoOcorrencia(this.ocorrencia, {required this.aoTocar, super.key});

  final OcorrenciaResumo ocorrencia;
  final VoidCallback aoTocar;

  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);
    final secundario = tema.colorScheme.onSurfaceVariant;
    final o = ocorrencia;
    return Card(
      child: InkWell(
        onTap: aoTocar,
        child: IntrinsicHeight(
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              ColoredBox(color: o.prioridade.cor(context.cores), child: const SizedBox(width: 4)),
              Expanded(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(14, 12, 14, 12),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Wrap: em telas estreitas ou com texto ampliado, o selo desce de linha.
                      Wrap(
                        alignment: WrapAlignment.spaceBetween,
                        crossAxisAlignment: WrapCrossAlignment.center,
                        spacing: 8,
                        runSpacing: 4,
                        children: [
                          Text(
                            o.numeroProtocolo,
                            style: estiloMono(
                              context,
                              base: tema.textTheme.labelMedium,
                            ).copyWith(color: secundario),
                          ),
                          SeloStatus(o.status),
                        ],
                      ),
                      const SizedBox(height: 6),
                      Text(o.natureza, style: tema.textTheme.titleMedium),
                      const SizedBox(height: 2),
                      Row(
                        children: [
                          Icon(Icons.place_outlined, size: 16, color: secundario),
                          const SizedBox(width: 4),
                          Expanded(
                            child: Text(
                              o.localizacao,
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: tema.textTheme.bodyMedium?.copyWith(color: secundario),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Wrap(
                        alignment: WrapAlignment.spaceBetween,
                        crossAxisAlignment: WrapCrossAlignment.center,
                        spacing: 12,
                        runSpacing: 4,
                        children: [
                          SeloPrioridade(o.prioridade),
                          Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(Icons.schedule, size: 14, color: secundario),
                              const SizedBox(width: 4),
                              Text(
                                context.dataHora(o.dataHoraFato),
                                style: tema.textTheme.bodySmall?.copyWith(color: secundario),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
