import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:shared_preferences_platform_interface/in_memory_shared_preferences_async.dart';
import 'package:shared_preferences_platform_interface/shared_preferences_async_platform_interface.dart';
import 'package:sgopi_mobile/features/preferencias/application/preferencias.dart';
import 'package:sgopi_mobile/features/preferencias/data/armazenamento_preferencias_local.dart';
import 'package:sgopi_mobile/features/preferencias/domain/preferencias.dart';

import '../../fakes/container.dart';

void main() {
  group('IdiomaApp', () {
    test('o escolhido vale; "sistema" segue o aparelho e cai em pt fora de pt/en', () {
      expect(IdiomaApp.en.resolver('pt'), 'en');
      expect(IdiomaApp.pt.resolver('en'), 'pt');
      expect(IdiomaApp.sistema.resolver('en'), 'en');
      expect(IdiomaApp.sistema.resolver('es'), 'pt');
    });

    test('código desconhecido ou ausente volta para "sistema"', () {
      expect(IdiomaApp.doCodigo('en'), IdiomaApp.en);
      expect(IdiomaApp.doCodigo(null), IdiomaApp.sistema);
      expect(IdiomaApp.doCodigo('fr'), IdiomaApp.sistema);
    });
  });

  group('ControladorPreferencias', () {
    test('abre com o que está salvo e grava cada mudança', () async {
      final d = Dubles()..preferencias.preferencias = const Preferencias(tema: ModoTema.escuro);
      final container = d.container();
      expect(container.read(controladorPreferenciasProvider).tema, ModoTema.escuro);

      await container.read(controladorPreferenciasProvider.notifier).definirIdioma(IdiomaApp.en);
      expect(container.read(controladorPreferenciasProvider).idioma, IdiomaApp.en);
      expect(d.preferencias.preferencias.idioma, IdiomaApp.en);
      expect(container.read(idiomaEfetivoProvider), 'en');
    });

    test('escolher o valor atual não grava de novo', () async {
      final d = Dubles();
      final container = d.container();
      await container.read(controladorPreferenciasProvider.notifier).definirTema(ModoTema.sistema);
      expect(d.preferencias.gravacoes, 0);
    });

    test('idioma "sistema" usa o idioma do aparelho no Accept-Language', () {
      final container = (Dubles()..idiomaDoAparelho = 'en').container();
      expect(container.read(idiomaEfetivoProvider), 'en');
    });
  });

  group('ArmazenamentoPreferenciasLocal', () {
    Future<SharedPreferencesWithCache> cache([Map<String, Object> dados = const {}]) {
      SharedPreferencesAsyncPlatform.instance = InMemorySharedPreferencesAsync.withData(dados);
      return SharedPreferencesWithCache.create(
        cacheOptions: const SharedPreferencesWithCacheOptions(allowList: ChavesPreferencias.todas),
      );
    }

    test('sem nada salvo, tudo segue o sistema', () async {
      expect(ArmazenamentoPreferenciasLocal(await cache()).carregar(), const Preferencias());
    });

    test('lê e grava com as chaves do web', () async {
      final armazenamento = ArmazenamentoPreferenciasLocal(
        await cache({'sgopi.tema': 'claro', 'sgopi.idioma': 'en'}),
      );
      expect(
        armazenamento.carregar(),
        const Preferencias(tema: ModoTema.claro, idioma: IdiomaApp.en),
      );

      await armazenamento.salvar(const Preferencias(tema: ModoTema.escuro));
      expect(armazenamento.carregar(), const Preferencias(tema: ModoTema.escuro));
    });

    test('valor corrompido não derruba o app', () async {
      final armazenamento = ArmazenamentoPreferenciasLocal(
        await cache({'sgopi.tema': 'roxo', 'sgopi.idioma': 'xx'}),
      );
      expect(armazenamento.carregar(), const Preferencias());
    });
  });
}
