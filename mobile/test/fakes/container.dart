import 'package:riverpod/misc.dart' show Override;
import 'package:riverpod/riverpod.dart';
import 'package:sgopi_mobile/core/aplicacao/dependencias.dart';
import 'package:sgopi_mobile/features/autenticacao/application/dependencias.dart';
import 'package:sgopi_mobile/features/ocorrencias/application/dependencias.dart';
import 'package:sgopi_mobile/features/revisao/application/dependencias.dart';

import 'fakes.dart';

/// Conjunto de fakes ligado às portas, no papel de `app/di.dart` nos testes.
final class Dubles {
  final relogio = RelogioFixo();
  final armazenamento = ArmazenamentoSessaoMemoria();
  final autenticacao = RepositorioAutenticacaoFake();
  final ocorrencias = RepositorioOcorrenciasFake();
  final revisao = RepositorioRevisaoFake();
  final localizacao = LocalizacaoFake();
  final seletor = SeletorImagemFake();

  List<Override> get substituicoes => [
    relogioProvider.overrideWithValue(relogio),
    armazenamentoSessaoProvider.overrideWithValue(armazenamento),
    repositorioAutenticacaoProvider.overrideWithValue(autenticacao),
    repositorioOcorrenciasProvider.overrideWithValue(ocorrencias),
    repositorioRevisaoProvider.overrideWithValue(revisao),
    portaLocalizacaoProvider.overrideWithValue(localizacao),
    portaSeletorImagemProvider.overrideWithValue(seletor),
  ];

  ProviderContainer container() =>
      ProviderContainer.test(overrides: substituicoes, retry: (_, _) => null);
}
