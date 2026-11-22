import 'package:material_ui/material_ui.dart';

/// Mesmo azul de destaque do frontend web (`--primary` em `frontend/src/styles.css`).
const _corInstitucional = Color(0xFF2563EB);

ThemeData temaClaro() => ThemeData(
  colorScheme: ColorScheme.fromSeed(seedColor: _corInstitucional),
  inputDecorationTheme: const InputDecorationTheme(border: OutlineInputBorder()),
);

ThemeData temaEscuro() => ThemeData(
  colorScheme: ColorScheme.fromSeed(seedColor: _corInstitucional, brightness: Brightness.dark),
  inputDecorationTheme: const InputDecorationTheme(border: OutlineInputBorder()),
);
