/// Página de resultados no formato `{itens, total, limit, offset}` do backend.
final class Pagina<T> {
  const Pagina({
    required this.itens,
    required this.total,
    required this.limite,
    required this.deslocamento,
  });

  final List<T> itens;
  final int total;
  final int limite;
  final int deslocamento;
}
