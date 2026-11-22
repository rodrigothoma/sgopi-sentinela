import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:material_ui/material_ui.dart';

import '../core/l10n/gerado/textos.dart';
import '../features/preferencias/application/preferencias.dart';
import '../features/preferencias/domain/preferencias.dart';
import 'roteador.dart';
import 'tema.dart';

class AppSgopi extends ConsumerWidget {
  const AppSgopi({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final preferencias = ref.watch(controladorPreferenciasProvider);
    final idioma = preferencias.idioma.codigo;
    return MaterialApp.router(
      onGenerateTitle: (context) => Textos.of(context).appTitulo,
      theme: temaClaro(),
      darkTheme: temaEscuro(),
      themeMode: switch (preferencias.tema) {
        ModoTema.sistema => ThemeMode.system,
        ModoTema.claro => ThemeMode.light,
        ModoTema.escuro => ThemeMode.dark,
      },
      locale: idioma == null ? null : Locale(idioma),
      localizationsDelegates: const [Textos.delegate, ...GlobalMaterialLocalizations.delegates],
      supportedLocales: Textos.supportedLocales,
      routerConfig: ref.watch(roteadorProvider),
    );
  }
}
