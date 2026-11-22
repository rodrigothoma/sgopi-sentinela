import 'package:riverpod/riverpod.dart';

import '../../../core/aplicacao/dependencias.dart';
import '../domain/portas.dart';
import 'decidir_revisao.dart';

/// Porta da revisão. O adaptador é ligado em `lib/app/di.dart`.
final repositorioRevisaoProvider = Provider<RepositorioRevisao>(
  (ref) => throw PortaNaoConfigurada('RepositorioRevisao'),
);

final decidirRevisaoProvider = Provider<DecidirRevisao>(
  (ref) => DecidirRevisao(ref.watch(repositorioRevisaoProvider)),
);
