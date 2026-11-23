import 'package:riverpod/riverpod.dart';

import '../domain/ocorrencia.dart';
import 'dependencias.dart';

const tamanhoPaginaOcorrencias = 20;

final class EstadoListaOcorrencias {
  const EstadoListaOcorrencias({
    required this.itens,
    required this.total,
    this.carregandoMais = false,
    this.erroAoCarregarMais,
  });

  final List<OcorrenciaResumo> itens;
  final int total;
  final bool carregandoMais;
  final Object? erroAoCarregarMais;

  bool get temMais => itens.length < total;

  EstadoListaOcorrencias copiar({
    List<OcorrenciaResumo>? itens,
    int? total,
    bool? carregandoMais,
    Object? erroAoCarregarMais,
  }) => EstadoListaOcorrencias(
    itens: itens ?? this.itens,
    total: total ?? this.total,
    carregandoMais: carregandoMais ?? this.carregandoMais,
    erroAoCarregarMais: erroAoCarregarMais,
  );
}

/// Lista paginada por filtro: "Minhas ocorrências" do Agente e fila do Delegado.
final listaOcorrenciasProvider =
    AsyncNotifierProvider.family<ListaOcorrencias, EstadoListaOcorrencias, FiltroOcorrencias>(
      ListaOcorrencias.new,
      isAutoDispose: true,
    );

class ListaOcorrencias extends AsyncNotifier<EstadoListaOcorrencias> {
  ListaOcorrencias(this.filtro);

  final FiltroOcorrencias filtro;

  @override
  Future<EstadoListaOcorrencias> build() async {
    final pagina = await ref
        .read(repositorioOcorrenciasProvider)
        .listar(filtro, limite: tamanhoPaginaOcorrencias, deslocamento: 0);
    return EstadoListaOcorrencias(itens: pagina.itens, total: pagina.total);
  }

  /// Rolagem infinita: busca a próxima página e mantém a atual se falhar.
  Future<void> carregarMais() async {
    final atual = state.value;
    if (atual == null || atual.carregandoMais || !atual.temMais) return;
    state = AsyncData(atual.copiar(carregandoMais: true));
    try {
      final pagina = await ref
          .read(repositorioOcorrenciasProvider)
          .listar(filtro, limite: tamanhoPaginaOcorrencias, deslocamento: atual.itens.length);
      state = AsyncData(
        atual.copiar(
          itens: [...atual.itens, ...pagina.itens],
          total: pagina.total,
          carregandoMais: false,
        ),
      );
    } on Exception catch (erro) {
      state = AsyncData(atual.copiar(carregandoMais: false, erroAoCarregarMais: erro));
    }
  }
}
