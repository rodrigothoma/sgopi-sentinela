import 'package:intl/intl.dart';
import 'package:material_ui/material_ui.dart';

import '../l10n/gerado/textos.dart';

extension ContextoApp on BuildContext {
  Textos get textos => Textos.of(this);

  /// Data e hora no fuso do aparelho, no formato do idioma ativo.
  String dataHora(DateTime instante) {
    final idioma = Localizations.localeOf(this).toLanguageTag();
    return DateFormat.yMd(idioma).add_Hm().format(instante.toLocal());
  }

  void avisar(String mensagem) {
    ScaffoldMessenger.of(this)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(mensagem)));
  }
}
