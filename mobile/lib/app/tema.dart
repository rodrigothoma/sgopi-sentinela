import 'package:flutter/services.dart';
import 'package:material_ui/material_ui.dart';

import '../core/apresentacao/design/cores_sgopi.dart';
import '../core/apresentacao/design/paleta.dart';
import '../core/apresentacao/design/tipografia.dart';

/// Temas claro e escuro com os tokens, fontes e raios do frontend web.
ThemeData temaClaro() => _tema(PaletaSgopi.claro, Brightness.light);

ThemeData temaEscuro() => _tema(PaletaSgopi.escuro, Brightness.dark);

const _raioControle = 10.0;
const _raioCartao = 14.0;
const _raioDialogo = 16.0;

ThemeData _tema(PaletaSgopi p, Brightness brilho) {
  final esquema = ColorScheme.fromSeed(seedColor: p.primaria, brightness: brilho).copyWith(
    primary: p.primaria,
    onPrimary: Colors.white,
    surface: p.superficie,
    onSurface: p.texto,
    onSurfaceVariant: p.textoSecundario,
    surfaceContainerLowest: p.fundo,
    surfaceContainerLow: p.superficie,
    surfaceContainer: p.cartao,
    surfaceContainerHigh: p.cartao,
    surfaceContainerHighest: p.linha,
    outline: p.linhaForte,
    outlineVariant: p.linha,
    error: p.perigo,
    onError: Colors.white,
    surfaceTint: Colors.transparent,
  );
  final texto = _tipografia(ThemeData(brightness: brilho).textTheme, p);
  final bordaControle = RoundedRectangleBorder(borderRadius: BorderRadius.circular(_raioControle));
  // Largura mínima finita: botões dentro de Row não podem pedir largura infinita.
  const tamanhoBotao = Size(64, 48);
  final escuro = brilho == Brightness.dark;

  return ThemeData(
    colorScheme: esquema,
    scaffoldBackgroundColor: p.fundo,
    fontFamily: Fontes.texto,
    textTheme: texto,
    extensions: [CoresSgopi.de(p)],
    dividerTheme: DividerThemeData(color: p.linha, space: 1),
    appBarTheme: AppBarThemeData(
      backgroundColor: p.fundo,
      foregroundColor: p.texto,
      surfaceTintColor: Colors.transparent,
      scrolledUnderElevation: 0,
      centerTitle: false,
      titleTextStyle: texto.titleLarge,
      systemOverlayStyle: escuro ? SystemUiOverlayStyle.light : SystemUiOverlayStyle.dark,
    ),
    cardTheme: CardThemeData(
      color: p.cartao,
      elevation: 0,
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(_raioCartao),
        side: BorderSide(color: p.linha),
      ),
      clipBehavior: Clip.antiAlias,
    ),
    inputDecorationTheme: InputDecorationThemeData(
      filled: true,
      fillColor: p.cartao,
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(_raioControle),
        borderSide: BorderSide(color: p.linha),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(_raioControle),
        borderSide: BorderSide(color: p.linha),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(_raioControle),
        borderSide: BorderSide(color: p.primaria, width: 2),
      ),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        minimumSize: tamanhoBotao,
        shape: bordaControle,
        textStyle: texto.labelLarge,
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        minimumSize: tamanhoBotao,
        shape: bordaControle,
        side: BorderSide(color: p.linhaForte),
        textStyle: texto.labelLarge,
      ),
    ),
    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(shape: bordaControle, textStyle: texto.labelLarge),
    ),
    floatingActionButtonTheme: FloatingActionButtonThemeData(
      backgroundColor: p.primaria,
      foregroundColor: Colors.white,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(_raioCartao)),
    ),
    chipTheme: ChipThemeData(
      shape: const StadiumBorder(),
      side: BorderSide(color: p.linha),
      backgroundColor: p.cartao,
      selectedColor: CoresSgopi.fundoDe(p.primaria),
      labelStyle: texto.labelLarge,
      showCheckmark: false,
    ),
    segmentedButtonTheme: SegmentedButtonThemeData(
      style: SegmentedButton.styleFrom(
        selectedBackgroundColor: CoresSgopi.fundoDe(p.primaria),
        selectedForegroundColor: p.primaria,
        side: BorderSide(color: p.linha),
      ),
    ),
    navigationBarTheme: NavigationBarThemeData(
      backgroundColor: p.superficie,
      surfaceTintColor: Colors.transparent,
      indicatorColor: CoresSgopi.fundoDe(p.primaria),
      labelTextStyle: WidgetStatePropertyAll(texto.labelMedium),
      iconTheme: WidgetStateProperty.resolveWith(
        (estados) => IconThemeData(
          color: estados.contains(WidgetState.selected) ? p.primaria : p.textoSecundario,
        ),
      ),
    ),
    listTileTheme: ListTileThemeData(
      iconColor: p.textoSecundario,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(_raioControle)),
    ),
    snackBarTheme: SnackBarThemeData(
      behavior: SnackBarBehavior.floating,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(_raioControle)),
    ),
    dialogTheme: DialogThemeData(
      backgroundColor: p.superficie,
      surfaceTintColor: Colors.transparent,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(_raioDialogo)),
      titleTextStyle: texto.headlineSmall,
    ),
    bottomSheetTheme: BottomSheetThemeData(
      backgroundColor: p.superficie,
      surfaceTintColor: Colors.transparent,
      showDragHandle: true,
    ),
  );
}

/// Rajdhani nos títulos (como `h1`–`h3` do web) e Plus Jakarta Sans no restante.
TextTheme _tipografia(TextTheme base, PaletaSgopi p) {
  TextStyle? destaque(TextStyle? estilo, double tamanho) => estilo?.copyWith(
    fontFamily: Fontes.destaque,
    fontWeight: FontWeight.w700,
    fontSize: tamanho,
    letterSpacing: 0.3,
  );
  final t = base.apply(fontFamily: Fontes.texto, bodyColor: p.texto, displayColor: p.texto);
  return t.copyWith(
    displaySmall: destaque(t.displaySmall, 34),
    headlineMedium: destaque(t.headlineMedium, 28),
    headlineSmall: destaque(t.headlineSmall, 24),
    titleLarge: destaque(t.titleLarge, 22),
    titleMedium: destaque(t.titleMedium, 18),
    titleSmall: destaque(t.titleSmall, 16),
  );
}
