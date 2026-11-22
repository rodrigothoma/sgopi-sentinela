import 'package:riverpod/riverpod.dart';

import '../../../core/aplicacao/dependencias.dart';
import '../domain/portas.dart';

/// Portas da autenticação. Os adaptadores são ligados em `lib/app/di.dart`.
final repositorioAutenticacaoProvider = Provider<RepositorioAutenticacao>(
  (ref) => throw PortaNaoConfigurada('RepositorioAutenticacao'),
);

final armazenamentoSessaoProvider = Provider<ArmazenamentoSessao>(
  (ref) => throw PortaNaoConfigurada('ArmazenamentoSessao'),
);
