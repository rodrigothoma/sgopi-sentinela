import 'dart:async';

import 'package:riverpod/riverpod.dart';

import '../../../core/aplicacao/dependencias.dart';
import '../domain/notificacao.dart';
import '../domain/portas.dart';

const tamanhoPaginaNotificacoes = 30;

/// Porta ligada em `lib/app/di.dart`.
final repositorioNotificacoesProvider = Provider<RepositorioNotificacoes>(
  (ref) => throw PortaNaoConfigurada('RepositorioNotificacoes'),
);

/// Intervalo de atualização do contador (o web usa 30 s; no celular, 60 s poupa bateria).
final intervaloContadorProvider = Provider<Duration>((ref) => const Duration(seconds: 60));

/// Não lidas, para o selo da aba. Atualiza sozinho enquanto alguém observa.
final naoLidasProvider = AsyncNotifierProvider<ContadorNaoLidas, int>(
  ContadorNaoLidas.new,
  isAutoDispose: true,
);

class ContadorNaoLidas extends AsyncNotifier<int> {
  @override
  Future<int> build() {
    final relogio = Timer(ref.watch(intervaloContadorProvider), ref.invalidateSelf);
    ref.onDispose(relogio.cancel);
    return ref.read(repositorioNotificacoesProvider).contarNaoLidas();
  }

  /// Ajuste local depois de marcar como lida, sem esperar o próximo ciclo.
  void descontar(int quantidade) {
    final atual = state.value;
    if (atual != null) state = AsyncData((atual - quantidade).clamp(0, atual));
  }
}

final class EstadoNotificacoes {
  const EstadoNotificacoes({
    required this.itens,
    required this.temMais,
    this.carregandoMais = false,
  });

  final List<Notificacao> itens;
  final bool temMais;
  final bool carregandoMais;

  EstadoNotificacoes copiar({List<Notificacao>? itens, bool? temMais, bool? carregandoMais}) =>
      EstadoNotificacoes(
        itens: itens ?? this.itens,
        temMais: temMais ?? this.temMais,
        carregandoMais: carregandoMais ?? this.carregandoMais,
      );
}

final listaNotificacoesProvider = AsyncNotifierProvider<ListaNotificacoes, EstadoNotificacoes>(
  ListaNotificacoes.new,
  isAutoDispose: true,
);

/// Lista paginada. O `total` do backend é só o tamanho da página, então há mais
/// páginas enquanto a última vier cheia.
class ListaNotificacoes extends AsyncNotifier<EstadoNotificacoes> {
  RepositorioNotificacoes get _repositorio => ref.read(repositorioNotificacoesProvider);

  @override
  Future<EstadoNotificacoes> build() async {
    final lote = await _repositorio.listar(limite: tamanhoPaginaNotificacoes, deslocamento: 0);
    return EstadoNotificacoes(
      itens: lote.itens,
      temMais: lote.itens.length == tamanhoPaginaNotificacoes,
    );
  }

  Future<void> carregarMais() async {
    final atual = state.value;
    if (atual == null || atual.carregandoMais || !atual.temMais) return;
    state = AsyncData(atual.copiar(carregandoMais: true));
    try {
      final lote = await _repositorio.listar(
        limite: tamanhoPaginaNotificacoes,
        deslocamento: atual.itens.length,
      );
      state = AsyncData(
        EstadoNotificacoes(
          itens: [...atual.itens, ...lote.itens],
          temMais: lote.itens.length == tamanhoPaginaNotificacoes,
        ),
      );
    } on Exception {
      // Mantém o que já foi carregado; a próxima rolagem tenta de novo.
      state = AsyncData(atual.copiar(carregandoMais: false));
    }
  }

  /// Otimista: marca na tela e desfaz se o backend recusar.
  Future<void> marcarLida(Notificacao notificacao) async {
    final atual = state.value;
    if (atual == null || notificacao.lida) return;
    state = AsyncData(atual.copiar(itens: _trocar(atual.itens, notificacao.id)));
    ref.read(naoLidasProvider.notifier).descontar(1);
    try {
      await _repositorio.marcarLida(notificacao.id);
    } on Exception {
      state = AsyncData(atual);
      ref.invalidate(naoLidasProvider);
      rethrow;
    }
  }

  Future<void> marcarTodasLidas() async {
    final atual = state.value;
    if (atual == null) return;
    await _repositorio.marcarTodasLidas();
    state = AsyncData(
      atual.copiar(itens: [for (final n in atual.itens) n.lida ? n : n.marcadaComoLida()]),
    );
    ref.invalidate(naoLidasProvider);
  }

  static List<Notificacao> _trocar(List<Notificacao> itens, String id) => [
    for (final n in itens) n.id == id ? n.marcadaComoLida() : n,
  ];
}
