import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:material_ui/material_ui.dart';

import '../../../core/apresentacao/contexto.dart';
import '../../../core/apresentacao/estado_erro.dart';
import '../../ocorrencias/application/detalhe_ocorrencia.dart';
import '../../ocorrencias/application/lista_ocorrencias.dart';
import '../../ocorrencias/domain/ocorrencia.dart';
import '../../ocorrencias/presentation/rotulos.dart';
import '../../ocorrencias/presentation/widgets/corpo_detalhe_ocorrencia.dart';
import '../application/dependencias.dart';
import '../domain/decisao_revisao.dart';
import 'dialogo_decisao.dart';

/// UC04: o Delegado lê a ocorrência e decide entre validar, devolver ou rejeitar.
class TelaRevisarOcorrencia extends ConsumerWidget {
  const TelaRevisarOcorrencia({required this.ocorrenciaId, super.key});

  final String ocorrenciaId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final provider = detalheOcorrenciaProvider(ocorrenciaId);
    final estado = ref.watch(provider);
    final ocorrencia = estado.value;
    return Scaffold(
      appBar: AppBar(title: Text(context.textos.revisarTitulo)),
      body: switch (estado) {
        AsyncValue(:final value?) => ListView(
          padding: const EdgeInsets.all(16),
          children: [CorpoDetalheOcorrencia(value), const SizedBox(height: 96)],
        ),
        AsyncValue(:final error?) => EstadoErro(
          mensagem: mensagemDeErro(context.textos, error),
          aoTentarNovamente: () => ref.invalidate(provider),
        ),
        _ => const Center(child: CircularProgressIndicator()),
      },
      bottomNavigationBar: ocorrencia != null && ocorrencia.status.aguardaRevisao
          ? _BarraDecisao(ocorrencia)
          : null,
    );
  }
}

class _BarraDecisao extends ConsumerStatefulWidget {
  const _BarraDecisao(this.ocorrencia);

  final OcorrenciaDetalhe ocorrencia;

  @override
  ConsumerState<_BarraDecisao> createState() => _BarraDecisaoState();
}

class _BarraDecisaoState extends ConsumerState<_BarraDecisao> {
  bool _enviando = false;

  Future<void> _decidir(TipoDecisao tipo) async {
    final decisao = await abrirDialogoDecisao(context, tipo);
    if (decisao == null || !mounted) return;
    setState(() => _enviando = true);
    try {
      final atualizada = await ref
          .read(decidirRevisaoProvider)
          .executar(widget.ocorrencia.id, decisao);
      ref.read(detalheOcorrenciaProvider(widget.ocorrencia.id).notifier).atualizarCom(atualizada);
      ref.invalidate(listaOcorrenciasProvider);
      if (!mounted) return;
      context.avisar(_mensagemSucesso(decisao));
      context.pop();
    } on Exception catch (erro) {
      if (mounted) context.avisar(mensagemDeErro(context.textos, erro));
    } finally {
      if (mounted) setState(() => _enviando = false);
    }
  }

  String _mensagemSucesso(DecisaoRevisao decisao) => switch (decisao) {
    Validar() => context.textos.decisaoValidada,
    Devolver() => context.textos.decisaoDevolvida,
    Rejeitar() => context.textos.decisaoRejeitada,
  };

  @override
  Widget build(BuildContext context) {
    final t = context.textos;
    final erro = Theme.of(context).colorScheme.error;
    VoidCallback? acao(TipoDecisao tipo) => _enviando ? null : () => _decidir(tipo);
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          children: [
            Expanded(
              child: TextButton(
                key: const Key('revisao.rejeitar'),
                onPressed: acao(TipoDecisao.rejeitar),
                style: TextButton.styleFrom(foregroundColor: erro),
                child: Text(t.acaoRejeitar),
              ),
            ),
            Expanded(
              child: OutlinedButton(
                key: const Key('revisao.devolver'),
                onPressed: acao(TipoDecisao.devolver),
                child: Text(t.acaoDevolver),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: FilledButton(
                key: const Key('revisao.validar'),
                onPressed: acao(TipoDecisao.validar),
                child: Text(t.acaoValidar),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
