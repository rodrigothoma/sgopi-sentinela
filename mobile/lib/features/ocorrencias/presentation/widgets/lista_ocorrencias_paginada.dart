import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:material_ui/material_ui.dart';

import '../../../../core/apresentacao/contexto.dart';
import '../../../../core/apresentacao/estado_erro.dart';
import '../../application/lista_ocorrencias.dart';
import '../../domain/ocorrencia.dart';
import '../rotulos.dart';
import 'cartao_ocorrencia.dart';

/// Distância do fim da lista a partir da qual a próxima página é pedida.
const _margemCarregamento = 300.0;

/// Lista com "puxar para atualizar" e rolagem infinita, reaproveitada pelo
/// Agente (minhas ocorrências) e pelo Delegado (fila de revisão).
class ListaOcorrenciasPaginada extends ConsumerWidget {
  const ListaOcorrenciasPaginada({
    required this.filtro,
    required this.mensagemVazia,
    required this.aoTocar,
    super.key,
  });

  final FiltroOcorrencias filtro;
  final String mensagemVazia;
  final void Function(OcorrenciaResumo) aoTocar;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final provider = listaOcorrenciasProvider(filtro);
    final estado = ref.watch(provider);
    Future<void> atualizar() => ref.refresh(provider.future);
    return switch (estado) {
      AsyncValue(:final value?) => RefreshIndicator(
        onRefresh: atualizar,
        child: _lista(context, ref, value),
      ),
      AsyncValue(:final error?) => EstadoErro(
        mensagem: mensagemDeErro(context.textos, error),
        aoTentarNovamente: atualizar,
      ),
      _ => const Center(child: CircularProgressIndicator()),
    };
  }

  Widget _lista(BuildContext context, WidgetRef ref, EstadoListaOcorrencias estado) {
    if (estado.itens.isEmpty) {
      return ListView(
        children: [
          Padding(
            padding: const EdgeInsets.all(48),
            child: Center(child: Text(mensagemVazia)),
          ),
        ],
      );
    }
    return NotificationListener<ScrollNotification>(
      onNotification: (aviso) {
        if (aviso.metrics.extentAfter < _margemCarregamento) {
          ref.read(listaOcorrenciasProvider(filtro).notifier).carregarMais();
        }
        return false;
      },
      child: ListView.builder(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.fromLTRB(12, 12, 12, 96),
        itemCount: estado.itens.length + 1,
        itemBuilder: (context, i) => i < estado.itens.length
            ? CartaoOcorrencia(estado.itens[i], aoTocar: () => aoTocar(estado.itens[i]))
            : _rodape(context, ref, estado),
      ),
    );
  }

  Widget _rodape(BuildContext context, WidgetRef ref, EstadoListaOcorrencias estado) {
    if (estado.carregandoMais) {
      return const Padding(
        padding: EdgeInsets.all(16),
        child: Center(child: CircularProgressIndicator()),
      );
    }
    if (estado.erroAoCarregarMais != null) {
      return TextButton(
        onPressed: () => ref.read(listaOcorrenciasProvider(filtro).notifier).carregarMais(),
        child: Text('${context.textos.erroCarregarMais} ${context.textos.tentarNovamente}'),
      );
    }
    return const SizedBox.shrink();
  }
}
