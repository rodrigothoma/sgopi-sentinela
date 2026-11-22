import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:material_ui/material_ui.dart';

import '../../../core/apresentacao/contexto.dart';
import '../../../core/apresentacao/estado_erro.dart';
import '../application/dependencias.dart';
import '../application/detalhe_ocorrencia.dart';
import '../domain/arquivo_evidencia.dart';
import '../domain/dados_ocorrencia.dart';
import '../domain/ocorrencia.dart';
import 'rotulos.dart';
import 'widgets/formulario_ocorrencia.dart';

/// Correção pelo Agente autor de uma ocorrência devolvida (`EM_CORRECAO`).
class TelaCorrigirOcorrencia extends ConsumerWidget {
  const TelaCorrigirOcorrencia({required this.ocorrenciaId, super.key});

  final String ocorrenciaId;

  Future<void> _salvar(
    BuildContext context,
    WidgetRef ref,
    OcorrenciaDetalhe atual,
    DadosOcorrencia dados,
    List<ArquivoEvidencia> evidencias,
  ) async {
    final resultado = await ref.read(corrigirOcorrenciaProvider).executar(atual, dados, evidencias);
    ref.read(detalheOcorrenciaProvider(ocorrenciaId).notifier).atualizarCom(resultado.ocorrencia);
    if (!context.mounted) return;
    final t = context.textos;
    final naoEnviadas = resultado.evidenciasNaoEnviadas.length;
    context.avisar(
      [t.correcaoSalva, if (naoEnviadas > 0) t.evidenciasNaoEnviadas(naoEnviadas)].join(' '),
    );
    context.pop();
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final provider = detalheOcorrenciaProvider(ocorrenciaId);
    return Scaffold(
      appBar: AppBar(title: Text(context.textos.corrigirTitulo)),
      body: switch (ref.watch(provider)) {
        AsyncValue(:final value?) => FormularioOcorrencia(
          inicial: value,
          evidenciasJaAnexadas: value.evidencias.length,
          rotuloEnviar: context.textos.salvarCorrecao,
          aoEnviar: (dados, evidencias) => _salvar(context, ref, value, dados, evidencias),
        ),
        AsyncValue(:final error?) => EstadoErro(
          mensagem: mensagemDeErro(context.textos, error),
          aoTentarNovamente: () => ref.invalidate(provider),
        ),
        _ => const Center(child: CircularProgressIndicator()),
      },
    );
  }
}
