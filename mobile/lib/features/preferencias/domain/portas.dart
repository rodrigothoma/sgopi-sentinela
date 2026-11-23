import 'preferencias.dart';

/// Porta de saída para guardar as preferências no aparelho.
abstract interface class ArmazenamentoPreferencias {
  /// Síncrono para o app abrir já no tema e idioma certos, sem piscar.
  Preferencias carregar();

  Future<void> salvar(Preferencias preferencias);
}
