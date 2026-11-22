import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/date_symbol_data_local.dart';
import 'package:material_ui/material_ui.dart';

import 'app/app.dart';
import 'app/di.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await initializeDateFormatting();
  runApp(
    ProviderScope(
      overrides: await adaptadoresDeProducao(),
      // Sem nova tentativa automática: erros de regra (403, 422) não mudam ao repetir,
      // e falhas de rede já oferecem "Tentar novamente" na tela.
      retry: (_, _) => null,
      child: const AppSgopi(),
    ),
  );
}
