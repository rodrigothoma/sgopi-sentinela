import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:material_ui/material_ui.dart';

import '../../../core/apresentacao/componentes/barra_acoes.dart';
import '../../../core/apresentacao/componentes/lista_carregando.dart';
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
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
          children: [CorpoDetalheOcorrencia(value)],
        ),
        AsyncValue(:final error?) => EstadoErro(
          mensagem: mensagemDeErro(context.textos, error),
          aoTentarNovamente: () => ref.invalidate(provider),
        ),
        _ => const ListaCarregando(quantidade: 3),
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
    final perigo = context.cores.perigo;
    VoidCallback? acao(TipoDecisao tipo) => _enviando ? null : () => _decidir(tipo);
    // Hierarquia: validar é a ação principal; rejeitar (definitiva) fica discreta e em vermelho.
    return BarraAcoes(
      child: Row(
        spacing: 8,
        children: [
          TextButton(
            key: const Key('revisao.rejeitar'),
            onPressed: acao(TipoDecisao.rejeitar),
            style: TextButton.styleFrom(foregroundColor: perigo),
            child: Text(t.acaoRejeitar),
          ),
          Expanded(
            child: OutlinedButton.icon(
              key: const Key('revisao.devolver'),
              onPressed: acao(TipoDecisao.devolver),
              icon: const Icon(Icons.undo),
              label: Text(t.acaoDevolver),
            ),
          ),
          Expanded(
            child: FilledButton.icon(
              key: const Key('revisao.validar'),
              onPressed: acao(TipoDecisao.validar),
              icon: const Icon(Icons.check),
              label: Text(t.acaoValidar),
            ),
          ),
        ],
      ),
    );
  }
}
