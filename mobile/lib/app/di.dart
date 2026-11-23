import 'dart:ui';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_riverpod/misc.dart' show Override;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../core/aplicacao/dependencias.dart';
import '../core/config/ambiente.dart';
import '../core/http/cliente_http.dart';
import '../features/autenticacao/application/controlador_sessao.dart';
import '../features/autenticacao/application/dependencias.dart';
import '../features/autenticacao/data/armazenamento_sessao_seguro.dart';
import '../features/autenticacao/data/repositorio_autenticacao_http.dart';
import '../features/notificacoes/application/notificacoes.dart';
import '../features/notificacoes/data/repositorio_notificacoes_http.dart';
import '../features/ocorrencias/application/dependencias.dart';
import '../features/ocorrencias/data/localizacao_geolocator.dart';
import '../features/ocorrencias/data/repositorio_ocorrencias_http.dart';
import '../features/ocorrencias/data/seletor_imagem_image_picker.dart';
import '../features/preferencias/application/preferencias.dart';
import '../features/preferencias/data/armazenamento_preferencias_local.dart';
import '../features/revisao/application/dependencias.dart';
import '../features/revisao/data/repositorio_revisao_http.dart';

/// COMPOSITION ROOT do app: o único lugar que instancia adaptadores concretos
/// e os liga às portas declaradas nas camadas `application/`.
/// Equivale ao `backend/src/infrastructure/di.py`.
Future<List<Override>> adaptadoresDeProducao() async {
  // Lido antes do primeiro quadro para o app já abrir no tema e idioma salvos.
  final preferencias = await SharedPreferencesWithCache.create(
    cacheOptions: const SharedPreferencesWithCacheOptions(allowList: ChavesPreferencias.todas),
  );
  final pacote = await PackageInfo.fromPlatform();
  return [
    versaoAppProvider.overrideWithValue('${pacote.version}+${pacote.buildNumber}'),
    armazenamentoSessaoProvider.overrideWithValue(
      ArmazenamentoSessaoSeguro(const FlutterSecureStorage()),
    ),
    armazenamentoPreferenciasProvider.overrideWithValue(
      ArmazenamentoPreferenciasLocal(preferencias),
    ),
    idiomaDoAparelhoProvider.overrideWithValue(PlatformDispatcher.instance.locale.languageCode),
    repositorioAutenticacaoProvider.overrideWith(
      (ref) => RepositorioAutenticacaoHttp(ref.watch(clienteHttpProvider)),
    ),
    repositorioOcorrenciasProvider.overrideWith(
      (ref) => RepositorioOcorrenciasHttp(ref.watch(clienteHttpProvider)),
    ),
    repositorioRevisaoProvider.overrideWith(
      (ref) => RepositorioRevisaoHttp(ref.watch(clienteHttpProvider)),
    ),
    repositorioNotificacoesProvider.overrideWith(
      (ref) => RepositorioNotificacoesHttp(ref.watch(clienteHttpProvider)),
    ),
    portaLocalizacaoProvider.overrideWithValue(const LocalizacaoGeolocator()),
    portaSeletorImagemProvider.overrideWithValue(SeletorImagemImagePicker()),
  ];
}

/// Cliente HTTP único, com o token e o idioma escolhido lidos a cada requisição.
final clienteHttpProvider = Provider<Dio>((ref) {
  final sessao = ref.read(controladorSessaoProvider.notifier);
  final dio = criarClienteHttp(
    urlBase: Ambiente.urlBaseApi,
    tokenAtual: sessao.tokenVigente,
    idioma: () => ref.read(idiomaEfetivoProvider),
    aoRecusarSessao: sessao.expirar,
  );
  ref.onDispose(dio.close);
  return dio;
});
