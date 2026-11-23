import 'package:riverpod/riverpod.dart';

import '../../../core/aplicacao/dependencias.dart';
import '../domain/portas.dart';
import 'corrigir_ocorrencia.dart';
import 'registrar_ocorrencia.dart';

/// Portas de ocorrências. Os adaptadores são ligados em `lib/app/di.dart`.
final repositorioOcorrenciasProvider = Provider<RepositorioOcorrencias>(
  (ref) => throw PortaNaoConfigurada('RepositorioOcorrencias'),
);

final portaLocalizacaoProvider = Provider<PortaLocalizacao>(
  (ref) => throw PortaNaoConfigurada('PortaLocalizacao'),
);

final portaSeletorImagemProvider = Provider<PortaSeletorImagem>(
  (ref) => throw PortaNaoConfigurada('PortaSeletorImagem'),
);

final registrarOcorrenciaProvider = Provider<RegistrarOcorrencia>(
  (ref) =>
      RegistrarOcorrencia(ref.watch(repositorioOcorrenciasProvider), ref.watch(relogioProvider)),
);

final corrigirOcorrenciaProvider = Provider<CorrigirOcorrencia>(
  (ref) =>
      CorrigirOcorrencia(ref.watch(repositorioOcorrenciasProvider), ref.watch(relogioProvider)),
);
