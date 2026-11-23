/// Enum cujo valor trafega na API com um código textual fixo (ex.: `AGUARDANDO_REVISAO`).
abstract interface class EnumApi {
  String get codigo;
}

/// Converte o código vindo da API no valor do enum.
///
/// Código desconhecido é erro de contrato entre app e backend, por isso falha
/// explicitamente em vez de cair num valor padrão silencioso.
T enumDeCodigo<T extends EnumApi>(List<T> valores, String codigo) {
  for (final valor in valores) {
    if (valor.codigo == codigo) return valor;
  }
  throw FormatException('Código "$codigo" desconhecido para $T.');
}
