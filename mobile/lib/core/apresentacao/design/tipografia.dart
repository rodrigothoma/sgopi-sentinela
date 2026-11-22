import 'package:material_ui/material_ui.dart';

/// Famílias do frontend web, embutidas em `assets/fontes/` (pubspec.yaml).
abstract final class Fontes {
  /// Texto corrido (`--font-sans`).
  static const texto = 'PlusJakartaSans';

  /// Títulos, marca e selos (`--font-display`).
  static const destaque = 'Rajdhani';

  /// Protocolos e hashes (`--font-mono`).
  static const mono = 'JetBrainsMono';
}

/// Protocolo, hash e outros identificadores técnicos.
TextStyle estiloMono(BuildContext context, {TextStyle? base}) =>
    (base ?? Theme.of(context).textTheme.bodyMedium!).copyWith(
      fontFamily: Fontes.mono,
      letterSpacing: 0,
    );
