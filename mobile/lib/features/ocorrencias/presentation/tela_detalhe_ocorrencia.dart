import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:material_ui/material_ui.dart';

import '../../../core/apresentacao/componentes/barra_acoes.dart';
import '../../../core/apresentacao/componentes/lista_carregando.dart';
import '../../../core/apresentacao/contexto.dart';
import '../../../core/apresentacao/estado_erro.dart';
import '../../../core/apresentacao/rotas.dart';
import '../../autenticacao/application/controlador_sessao.dart';
import '../../autenticacao/domain/permissao.dart';
import '../application/dependencias.dart';
import '../application/detalhe_ocorrencia.dart';
import '../application/lista_ocorrencias.dart';
import '../domain/ocorrencia.dart';
import '../domain/portas.dart';
import 'rotulos.dart';
import 'widgets/corpo_detalhe_ocorrencia.dart';

/// Detalhe para o Agente autor, com os atos permitidos pelo status atual.
class TelaDetalheOcorrencia extends ConsumerWidget {
  const TelaDetalheOcorrencia({required this.ocorrenciaId, super.key});

  final String ocorrenciaId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final provider = detalheOcorrenciaProvider(ocorrenciaId);
    final estado = ref.watch(provider);
    return Scaffold(
      appBar: AppBar(title: Text(context.textos.detalheTitulo)),
      body: switch (estado) {
        AsyncValue(:final value?) => RefreshIndicator(
          onRefresh: () => ref.refresh(provider.future),
          child: ListView(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
            children: [CorpoDetalheOcorrencia(value)],
          ),
        ),
        AsyncValue(:final error?) => EstadoErro(
          mensagem: mensagemDeErro(context.textos, error),
          aoTentarNovamente: () => ref.invalidate(provider),
        ),
        _ => const ListaCarregando(quantidade: 3),
      },
      bottomNavigationBar: estado.value == null ? null : _AcoesAgente(estado.value!),
    );
  }
}

class _AcoesAgente extends ConsumerStatefulWidget {
  const _AcoesAgente(this.ocorrencia);

  final OcorrenciaDetalhe ocorrencia;

  @override
  ConsumerState<_AcoesAgente> createState() => _AcoesAgenteState();
}

class _AcoesAgenteState extends ConsumerState<_AcoesAgente> {
  bool _ocupado = false;

  DetalheOcorrencia get _controlador =>
      ref.read(detalheOcorrenciaProvider(widget.ocorrencia.id).notifier);

  Future<void> _executar(Future<void> Function() acao, String sucesso) async {
    setState(() => _ocupado = true);
    try {
      await acao();
      ref.invalidate(listaOcorrenciasProvider);
      if (mounted) context.avisar(sucesso);
    } on Exception catch (erro) {
      if (mounted) context.avisar(mensagemDeErro(context.textos, erro));
    } finally {
      if (mounted) setState(() => _ocupado = false);
    }
  }

  Future<void> _anexarFoto() async {
    final arquivo = await ref.read(portaSeletorImagemProvider).selecionar(OrigemImagem.camera);
    if (arquivo == null || !mounted) return;
    await _executar(() => _controlador.anexar(arquivo), context.textos.evidenciaAnexada);
  }

  Future<void> _reenviar() async {
    final t = context.textos;
    final confirmado = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        content: Text(t.reenviarConfirmacao),
        actions: [
          TextButton(onPressed: () => Navigator.of(context).pop(false), child: Text(t.cancelar)),
          FilledButton(onPressed: () => Navigator.of(context).pop(true), child: Text(t.confirmar)),
        ],
      ),
    );
    if (confirmado ?? false) await _executar(_controlador.reenviar, t.reenviada);
  }

  @override
  Widget build(BuildContext context) {
    final t = context.textos;
    final status = widget.ocorrencia.status;
    final ehAgente =
        ref.watch(sessaoAtualProvider)?.usuario.papel.pode(Permissao.registrarOcorrencia) ?? false;
    final acoes = <Widget>[
      if (status.aceitaEvidencia)
        OutlinedButton.icon(
          onPressed: _ocupado ? null : _anexarFoto,
          icon: const Icon(Icons.add_a_photo_outlined),
          label: Text(t.acaoAnexarFoto),
        ),
      if (status.aceitaCorrecao) ...[
        OutlinedButton.icon(
          onPressed: _ocupado
              ? null
              : () => context.push(Rotas.corrigirOcorrencia(widget.ocorrencia.id)),
          icon: const Icon(Icons.edit_outlined),
          label: Text(t.acaoCorrigir),
        ),
        FilledButton.icon(
          onPressed: _ocupado ? null : _reenviar,
          icon: const Icon(Icons.send),
          label: Text(t.acaoReenviar),
        ),
      ],
    ];
    if (!ehAgente || acoes.isEmpty) return const SizedBox.shrink();
    return BarraAcoes(
      child: Wrap(alignment: WrapAlignment.end, spacing: 8, runSpacing: 8, children: acoes),
    );
  }
}
