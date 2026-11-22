import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:material_ui/material_ui.dart';

import '../core/l10n/gerado/textos.dart';
import 'roteador.dart';
import 'tema.dart';

class AppSgopi extends ConsumerWidget {
  const AppSgopi({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) => MaterialApp.router(
    onGenerateTitle: (context) => Textos.of(context).appTitulo,
    theme: temaClaro(),
    darkTheme: temaEscuro(),
    localizationsDelegates: const [Textos.delegate, ...GlobalMaterialLocalizations.delegates],
    supportedLocales: Textos.supportedLocales,
    routerConfig: ref.watch(roteadorProvider),
  );
}
