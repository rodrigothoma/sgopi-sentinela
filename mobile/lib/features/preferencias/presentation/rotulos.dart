import 'package:material_ui/material_ui.dart';

import '../../../core/l10n/gerado/textos.dart';
import '../domain/preferencias.dart';

extension RotuloModoTema on ModoTema {
  String rotulo(Textos t) => switch (this) {
    ModoTema.sistema => t.temaSistema,
    ModoTema.claro => t.temaClaro,
    ModoTema.escuro => t.temaEscuro,
  };

  IconData get icone => switch (this) {
    ModoTema.sistema => Icons.brightness_auto_outlined,
    ModoTema.claro => Icons.light_mode_outlined,
    ModoTema.escuro => Icons.dark_mode_outlined,
  };
}

extension RotuloIdioma on IdiomaApp {
  /// Cada idioma aparece no próprio idioma (endônimo), como nos ajustes do sistema.
  String rotulo(Textos t) => switch (this) {
    IdiomaApp.sistema => t.idiomaSistema,
    IdiomaApp.pt => 'Português',
    IdiomaApp.en => 'English',
  };
}
