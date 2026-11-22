import 'package:material_ui/material_ui.dart';

/// Tokens de cor do frontend web (`frontend/src/styles.css`), um conjunto por tema.
/// As telas não usam estes valores direto: leem `Theme.of(context).colorScheme`
/// ou `context.cores` ([CoresSgopi]).
final class PaletaSgopi {
  const PaletaSgopi({
    required this.fundo,
    required this.superficie,
    required this.cartao,
    required this.texto,
    required this.textoSecundario,
    required this.linha,
    required this.linhaForte,
    required this.primaria,
    required this.sucesso,
    required this.aviso,
    required this.perigo,
    required this.correcao,
    required this.urgente,
    required this.alta,
    required this.neutro,
  });

  final Color fundo; // --bg
  final Color superficie; // --bg-surface
  final Color cartao; // --card
  final Color texto; // --ink
  final Color textoSecundario; // --muted
  final Color linha; // --line
  final Color linhaForte; // --line-soft
  final Color primaria; // --primary
  final Color sucesso; // --ok
  final Color aviso; // --warn
  final Color perigo; // --danger
  final Color correcao; // .status-EM_CORRECAO
  final Color urgente; // .prioridade-URGENTE
  final Color alta; // .prioridade-ALTA
  final Color neutro; // .status-ENCERRADA

  static const claro = PaletaSgopi(
    fundo: Color(0xFFF8FAFC),
    superficie: Color(0xFFFFFFFF),
    cartao: Color(0xFFFFFFFF),
    texto: Color(0xFF0F172A),
    textoSecundario: Color(0xFF64748B),
    linha: Color(0xFFE2E8F0),
    linhaForte: Color(0xFFCBD5E1),
    primaria: Color(0xFF2563EB),
    sucesso: Color(0xFF059669),
    aviso: Color(0xFFD97706),
    perigo: Color(0xFFDC2626),
    correcao: Color(0xFFC2410C),
    urgente: Color(0xFFDC2626),
    alta: Color(0xFFC2410C),
    neutro: Color(0xFF64748B),
  );

  static const escuro = PaletaSgopi(
    fundo: Color(0xFF121214),
    superficie: Color(0xFF18181B),
    cartao: Color(0xFF202024),
    texto: Color(0xFFF4F4F5),
    textoSecundario: Color(0xFFA1A1AA),
    linha: Color(0xFF2E2E33),
    linhaForte: Color(0xFF3F3F46),
    primaria: Color(0xFF3B82F6),
    sucesso: Color(0xFF10B981),
    aviso: Color(0xFFF59E0B),
    perigo: Color(0xFFEF4444),
    correcao: Color(0xFFEA580C),
    urgente: Color(0xFFF87171),
    alta: Color(0xFFFB923C),
    neutro: Color(0xFF94A3B8),
  );
}
