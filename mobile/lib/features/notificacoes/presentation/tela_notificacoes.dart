import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:material_ui/material_ui.dart';

import '../../../core/aplicacao/dependencias.dart';
import '../../../core/apresentacao/componentes/estado_vazio.dart';
import '../../../core/apresentacao/componentes/lista_carregando.dart';
import '../../../core/apresentacao/contexto.dart';
import '../../../core/apresentacao/estado_erro.dart';
import '../../../core/apresentacao/mensagem_falha.dart';
import '../../../core/apresentacao/rotas.dart';
import '../../../core/dominio/falha.dart';
import '../../autenticacao/application/controlador_sessao.dart';
import '../../autenticacao/domain/permissao.dart';
import '../application/notificacoes.dart';
import '../domain/notificacao.dart';

/// Avisos do usuário; tocar marca como lido e abre a ocorrência citada.
class TelaNotificacoes extends ConsumerWidget {
  const TelaNotificacoes({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = context.textos;
    final estado = ref.watch(listaNotificacoesProvider);
    final temNaoLidas = estado.value?.itens.any((n) => !n.lida) ?? false;
    Future<void> atualizar() async {
      ref.invalidate(naoLidasProvider);
      return ref.refresh(listaNotificacoesProvider.future).then((_) {});
    }

    return Scaffold(
      appBar: AppBar(
        title: Text(t.abaNotificacoes),
        actions: [
          if (temNaoLidas)
            IconButton(
              key: const Key('notificacoes.marcarTodas'),
              tooltip: t.marcarTodasLidas,
              icon: const Icon(Icons.done_all),
              onPressed: () => _marcarTodas(context, ref),
            ),
        ],
      ),
      body: switch (estado) {
        AsyncValue(:final value?) => RefreshIndicator(
          onRefresh: atualizar,
          child: value.itens.isEmpty
              ? LayoutBuilder(
                  builder: (context, limites) => SingleChildScrollView(
                    physics: const AlwaysScrollableScrollPhysics(),
                    child: SizedBox(
                      height: limites.maxHeight,
                      child: EstadoVazio(
                        icone: Icons.notifications_none,
                        titulo: t.notificacoesVazias,
                        mensagem: t.notificacoesVaziasDica,
                      ),
                    ),
                  ),
                )
              : _Lista(value),
        ),
        AsyncValue(:final error?) => EstadoErro(
          mensagem: _mensagem(context, error),
          aoTentarNovamente: atualizar,
        ),
        _ => const ListaCarregando(),
      },
    );
  }

  Future<void> _marcarTodas(BuildContext context, WidgetRef ref) async {
    try {
      await ref.read(listaNotificacoesProvider.notifier).marcarTodasLidas();
      if (context.mounted) context.avisar(context.textos.todasMarcadasLidas);
    } on Exception catch (erro) {
      if (context.mounted) context.avisar(_mensagem(context, erro));
    }
  }
}

String _mensagem(BuildContext context, Object erro) =>
    erro is Falha ? mensagemDeFalha(context.textos, erro) : context.textos.erroInesperado;

class _Lista extends ConsumerWidget {
  const _Lista(this.estado);

  final EstadoNotificacoes estado;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final agora = ref.watch(relogioProvider).agora();
    return NotificationListener<ScrollNotification>(
      onNotification: (aviso) {
        if (aviso.metrics.extentAfter < 300) {
          ref.read(listaNotificacoesProvider.notifier).carregarMais();
        }
        return false;
      },
      child: ListView.separated(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.symmetric(vertical: 8),
        itemCount: estado.itens.length + (estado.carregandoMais ? 1 : 0),
        separatorBuilder: (_, _) => const Divider(indent: 72),
        itemBuilder: (context, i) => i < estado.itens.length
            ? _ItemNotificacao(estado.itens[i], agora: agora)
            : const Padding(
                padding: EdgeInsets.all(16),
                child: Center(child: CircularProgressIndicator()),
              ),
      ),
    );
  }
}

class _ItemNotificacao extends ConsumerWidget {
  const _ItemNotificacao(this.notificacao, {required this.agora});

  final Notificacao notificacao;
  final DateTime agora;

  Future<void> _abrir(BuildContext context, WidgetRef ref) async {
    final ocorrencia = notificacao.ocorrenciaVinculada;
    final podeRevisar =
        ref.read(sessaoAtualProvider)?.usuario.papel.pode(Permissao.revisarOcorrencia) ?? false;
    try {
      await ref.read(listaNotificacoesProvider.notifier).marcarLida(notificacao);
    } on Exception catch (erro) {
      if (context.mounted) context.avisar(_mensagem(context, erro));
    }
    if (ocorrencia != null && context.mounted) {
      await context.push(Rotas.ocorrencia(ocorrencia, podeRevisar: podeRevisar));
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final tema = Theme.of(context);
    final cores = context.cores;
    final n = notificacao;
    final destaque = n.importante ? cores.perigo : tema.colorScheme.primary;
    return ListTile(
      key: Key('notificacao.${n.id}'),
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      leading: CircleAvatar(
        backgroundColor: destaque.withValues(alpha: 0.12),
        foregroundColor: destaque,
        child: Icon(_icone(n.tipo)),
      ),
      title: Row(
        children: [
          Expanded(
            child: Text(
              n.titulo,
              style: tema.textTheme.bodyLarge?.copyWith(
                fontWeight: n.lida ? FontWeight.w400 : FontWeight.w700,
              ),
            ),
          ),
          if (!n.lida)
            Container(
              key: const Key('notificacao.naoLida'),
              width: 10,
              height: 10,
              margin: const EdgeInsets.only(left: 8),
              decoration: BoxDecoration(color: tema.colorScheme.primary, shape: BoxShape.circle),
            ),
        ],
      ),
      subtitle: Text(
        '${n.mensagem}\n${context.tempoRelativo(n.criadaEm, agora)}',
        maxLines: 3,
        overflow: TextOverflow.ellipsis,
      ),
      isThreeLine: true,
      onTap: () => _abrir(context, ref),
    );
  }

  static IconData _icone(String tipo) => switch (tipo) {
    'NOVA_OCORRENCIA' => Icons.assignment_late_outlined,
    'REVISAO_OCORRENCIA' => Icons.fact_check_outlined,
    'DESPACHO' => Icons.local_police_outlined,
    'ALERTA_CRITICIDADE' => Icons.warning_amber_outlined,
    _ => Icons.notifications_outlined,
  };
}
