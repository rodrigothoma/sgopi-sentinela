import 'package:riverpod/riverpod.dart';

import '../../../core/aplicacao/dependencias.dart';
import '../domain/portas.dart';
import '../domain/preferencias.dart';

/// Porta ligada em `lib/app/di.dart`.
final armazenamentoPreferenciasProvider = Provider<ArmazenamentoPreferencias>(
  (ref) => throw PortaNaoConfigurada('ArmazenamentoPreferencias'),
);

/// Idioma do aparelho (código de duas letras), ligado em `lib/app/di.dart`.
final idiomaDoAparelhoProvider = Provider<String>((ref) => 'pt');

final controladorPreferenciasProvider = NotifierProvider<ControladorPreferencias, Preferencias>(
  ControladorPreferencias.new,
);

/// Tema e idioma do app; a mudança vale na hora e fica salva no aparelho.
class ControladorPreferencias extends Notifier<Preferencias> {
  @override
  Preferencias build() => ref.watch(armazenamentoPreferenciasProvider).carregar();

  Future<void> definirTema(ModoTema tema) => _aplicar(state.copyWith(tema: tema));

  Future<void> definirIdioma(IdiomaApp idioma) => _aplicar(state.copyWith(idioma: idioma));

  Future<void> _aplicar(Preferencias novas) async {
    if (novas == state) return;
    state = novas;
    await ref.read(armazenamentoPreferenciasProvider).salvar(novas);
  }
}

/// Idioma efetivo da interface e do `Accept-Language` enviado ao backend.
final idiomaEfetivoProvider = Provider<String>(
  (ref) => ref
      .watch(controladorPreferenciasProvider.select((p) => p.idioma))
      .resolver(ref.watch(idiomaDoAparelhoProvider)),
);
