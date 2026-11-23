import 'package:shared_preferences/shared_preferences.dart';

import '../domain/portas.dart';
import '../domain/preferencias.dart';

/// Chaves com os mesmos nomes usados no localStorage do frontend web.
abstract final class ChavesPreferencias {
  static const tema = 'sgopi.tema';
  static const idioma = 'sgopi.idioma';
  static const todas = {tema, idioma};
}

/// Preferências em `SharedPreferences` (não são dados sensíveis, ao contrário da sessão).
final class ArmazenamentoPreferenciasLocal implements ArmazenamentoPreferencias {
  ArmazenamentoPreferenciasLocal(this._cache);

  final SharedPreferencesWithCache _cache;

  @override
  Preferencias carregar() {
    final tema = _cache.getString(ChavesPreferencias.tema);
    return Preferencias(
      tema: ModoTema.values.firstWhere((m) => m.name == tema, orElse: () => ModoTema.sistema),
      idioma: IdiomaApp.doCodigo(_cache.getString(ChavesPreferencias.idioma)),
    );
  }

  @override
  Future<void> salvar(Preferencias preferencias) async {
    await _cache.setString(ChavesPreferencias.tema, preferencias.tema.name);
    final idioma = preferencias.idioma.codigo;
    if (idioma == null) {
      await _cache.remove(ChavesPreferencias.idioma);
    } else {
      await _cache.setString(ChavesPreferencias.idioma, idioma);
    }
  }
}
