import 'package:intl/intl.dart';
import 'package:material_ui/material_ui.dart';

import '../l10n/gerado/textos.dart';
import 'design/cores_sgopi.dart';

extension ContextoApp on BuildContext {
  Textos get textos => Textos.of(this);

  CoresSgopi get cores => Theme.of(this).extension<CoresSgopi>()!;

  String get _idioma => Localizations.localeOf(this).toLanguageTag();

  /// Data e hora no fuso do aparelho, no formato do idioma ativo.
  String dataHora(DateTime instante) => DateFormat.yMd(_idioma).add_Hm().format(instante.toLocal());

  String hora(DateTime instante) => DateFormat.Hm(_idioma).format(instante.toLocal());

  /// "há 5 min", "há 3 h"; depois de uma semana, a data completa.
  String tempoRelativo(DateTime instante, DateTime agora) {
    final t = textos;
    final passado = agora.difference(instante);
    if (passado.inMinutes < 1) return t.tempoAgora;
    if (passado.inHours < 1) return t.tempoMinutos(passado.inMinutes);
    if (passado.inDays < 1) return t.tempoHoras(passado.inHours);
    if (passado.inDays < 7) return t.tempoDias(passado.inDays);
    return dataHora(instante);
  }

  void avisar(String mensagem) {
    ScaffoldMessenger.of(this)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(mensagem)));
  }
}
