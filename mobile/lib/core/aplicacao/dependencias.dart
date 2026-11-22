import 'package:riverpod/riverpod.dart';

import '../dominio/relogio.dart';

/// Erro de montagem: uma porta foi lida sem que `app/di.dart` a tenha ligado a um adaptador.
final class PortaNaoConfigurada extends Error {
  PortaNaoConfigurada(this.porta);

  final String porta;

  @override
  String toString() => 'Porta "$porta" sem adaptador: configure-a em lib/app/di.dart.';
}

final relogioProvider = Provider<Relogio>((ref) => const RelogioDoSistema());
