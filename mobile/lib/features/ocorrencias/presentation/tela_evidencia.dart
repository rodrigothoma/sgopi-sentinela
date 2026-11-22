import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:material_ui/material_ui.dart';

import '../../../core/apresentacao/contexto.dart';
import '../../../core/apresentacao/estado_erro.dart';
import '../application/conteudo_evidencia.dart';
import '../domain/ocorrencia.dart';
import 'rotulos.dart';

/// Abre a foto em tela cheia sobre a tela atual (detalhe do Agente ou revisão do Delegado).
Future<void> abrirEvidencia(BuildContext context, String ocorrenciaId, Evidencia evidencia) =>
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        fullscreenDialog: true,
        builder: (_) => TelaEvidencia(ocorrenciaId: ocorrenciaId, evidencia: evidencia),
      ),
    );

/// Visualização da foto com zoom por pinça. O arquivo fica só em memória, nunca no aparelho.
class TelaEvidencia extends ConsumerWidget {
  const TelaEvidencia({required this.ocorrenciaId, required this.evidencia, super.key});

  final String ocorrenciaId;
  final Evidencia evidencia;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = context.textos;
    final referencia = (ocorrenciaId: ocorrenciaId, evidenciaId: evidencia.id);
    final conteudo = ref.watch(conteudoEvidenciaProvider(referencia));
    return Theme(
      data: ThemeData(
        colorSchemeSeed: Theme.of(context).colorScheme.primary,
        brightness: Brightness.dark,
      ),
      child: Scaffold(
        backgroundColor: Colors.black,
        appBar: AppBar(
          backgroundColor: Colors.black,
          title: Text(evidencia.nomeOriginal, overflow: TextOverflow.ellipsis),
          bottom: PreferredSize(
            preferredSize: const Size.fromHeight(20),
            child: Text(context.dataHora(evidencia.enviadaEm)),
          ),
        ),
        body: conteudo.when(
          data: (bytes) => InteractiveViewer(
            maxScale: 6,
            child: Center(
              child: Image.memory(
                bytes,
                key: const Key('evidencia.imagem'),
                errorBuilder: (context, _, _) => Text(t.imagemIlegivel),
              ),
            ),
          ),
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (erro, _) => EstadoErro(
            mensagem: mensagemDeErro(t, erro),
            aoTentarNovamente: () => ref.invalidate(conteudoEvidenciaProvider(referencia)),
          ),
        ),
      ),
    );
  }
}
