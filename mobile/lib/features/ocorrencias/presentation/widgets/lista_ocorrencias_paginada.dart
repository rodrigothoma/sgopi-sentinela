import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:material_ui/material_ui.dart';

import '../../../../core/apresentacao/componentes/estado_vazio.dart';
import '../../../../core/apresentacao/componentes/lista_carregando.dart';
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
    this.dicaVazia,
    this.iconeVazio = Icons.inbox_outlined,
    super.key,
  });

  final FiltroOcorrencias filtro;
  final String mensagemVazia;
  final String? dicaVazia;
  final IconData iconeVazio;
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
      _ => const ListaCarregando(),
    };
  }

  Widget _lista(BuildContext context, WidgetRef ref, EstadoListaOcorrencias estado) {
    if (estado.itens.isEmpty) {
      // Rolável para o "puxar para atualizar" funcionar também com a lista vazia.
      return LayoutBuilder(
        builder: (context, limites) => SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          child: SizedBox(
            height: limites.maxHeight,
            child: EstadoVazio(icone: iconeVazio, titulo: mensagemVazia, mensagem: dicaVazia),
          ),
        ),
      );
    }
    return NotificationListener<ScrollNotification>(
      onNotification: (aviso) {
        if (aviso.metrics.extentAfter < _margemCarregamento) {
          ref.read(listaOcorrenciasProvider(filtro).notifier).carregarMais();
        }
        return false;
      },
      child: ListView.separated(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 96),
        itemCount: estado.itens.length + 1,
        separatorBuilder: (_, _) => const SizedBox(height: 12),
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
        child: Text(context.textos.carregarMaisFalhou, textAlign: TextAlign.center),
      );
    }
    return const SizedBox.shrink();
  }
}
