import 'package:material_ui/material_ui.dart';

import 'paleta.dart';

/// Cores semânticas que o `ColorScheme` do Material não tem (sucesso, aviso,
/// correção, prioridades). Acesso nas telas por `context.cores`.
@immutable
final class CoresSgopi extends ThemeExtension<CoresSgopi> {
  const CoresSgopi({
    required this.sucesso,
    required this.aviso,
    required this.perigo,
    required this.correcao,
    required this.informacao,
    required this.neutro,
    required this.urgente,
    required this.alta,
    required this.linha,
  });

  factory CoresSgopi.de(PaletaSgopi p) => CoresSgopi(
    sucesso: p.sucesso,
    aviso: p.aviso,
    perigo: p.perigo,
    correcao: p.correcao,
    informacao: p.primaria,
    neutro: p.neutro,
    urgente: p.urgente,
    alta: p.alta,
    linha: p.linha,
  );

  final Color sucesso;
  final Color aviso;
  final Color perigo;
  final Color correcao;
  final Color informacao;
  final Color neutro;
  final Color urgente;
  final Color alta;
  final Color linha;

  /// Fundo translúcido para selos e destaques sobre a cor [cor].
  static Color fundoDe(Color cor) => cor.withValues(alpha: 0.14);

  @override
  CoresSgopi copyWith({
    Color? sucesso,
    Color? aviso,
    Color? perigo,
    Color? correcao,
    Color? informacao,
    Color? neutro,
    Color? urgente,
    Color? alta,
    Color? linha,
  }) => CoresSgopi(
    sucesso: sucesso ?? this.sucesso,
    aviso: aviso ?? this.aviso,
    perigo: perigo ?? this.perigo,
    correcao: correcao ?? this.correcao,
    informacao: informacao ?? this.informacao,
    neutro: neutro ?? this.neutro,
    urgente: urgente ?? this.urgente,
    alta: alta ?? this.alta,
    linha: linha ?? this.linha,
  );

  @override
  CoresSgopi lerp(CoresSgopi? outro, double t) {
    if (outro == null) return this;
    Color c(Color a, Color b) => Color.lerp(a, b, t)!;
    return CoresSgopi(
      sucesso: c(sucesso, outro.sucesso),
      aviso: c(aviso, outro.aviso),
      perigo: c(perigo, outro.perigo),
      correcao: c(correcao, outro.correcao),
      informacao: c(informacao, outro.informacao),
      neutro: c(neutro, outro.neutro),
      urgente: c(urgente, outro.urgente),
      alta: c(alta, outro.alta),
      linha: c(linha, outro.linha),
    );
  }
}
