/// Fonte do instante atual, injetável para tornar regras temporais testáveis.
abstract interface class Relogio {
  DateTime agora();
}

final class RelogioDoSistema implements Relogio {
  const RelogioDoSistema();

  @override
  DateTime agora() => DateTime.now().toUtc();
}
