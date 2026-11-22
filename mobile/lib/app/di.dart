import 'dart:ui';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_riverpod/misc.dart' show Override;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../core/config/ambiente.dart';
import '../core/http/cliente_http.dart';
import '../features/autenticacao/application/controlador_sessao.dart';
import '../features/autenticacao/application/dependencias.dart';
import '../features/autenticacao/data/armazenamento_sessao_seguro.dart';
import '../features/autenticacao/data/repositorio_autenticacao_http.dart';
import '../features/ocorrencias/application/dependencias.dart';
import '../features/ocorrencias/data/localizacao_geolocator.dart';
import '../features/ocorrencias/data/repositorio_ocorrencias_http.dart';
import '../features/ocorrencias/data/seletor_imagem_image_picker.dart';
import '../features/revisao/application/dependencias.dart';
import '../features/revisao/data/repositorio_revisao_http.dart';

/// COMPOSITION ROOT do app: o único lugar que instancia adaptadores concretos
/// e os liga às portas declaradas nas camadas `application/`.
/// Equivale ao `backend/src/infrastructure/di.py`.
List<Override> adaptadoresDeProducao() => [
  armazenamentoSessaoProvider.overrideWithValue(
    ArmazenamentoSessaoSeguro(const FlutterSecureStorage()),
  ),
  repositorioAutenticacaoProvider.overrideWith(
    (ref) => RepositorioAutenticacaoHttp(ref.watch(clienteHttpProvider)),
  ),
  repositorioOcorrenciasProvider.overrideWith(
    (ref) => RepositorioOcorrenciasHttp(ref.watch(clienteHttpProvider)),
  ),
  repositorioRevisaoProvider.overrideWith(
    (ref) => RepositorioRevisaoHttp(ref.watch(clienteHttpProvider)),
  ),
  portaLocalizacaoProvider.overrideWithValue(const LocalizacaoGeolocator()),
  portaSeletorImagemProvider.overrideWithValue(SeletorImagemImagePicker()),
];

/// Cliente HTTP único, com o token e o idioma lidos a cada requisição.
final clienteHttpProvider = Provider<Dio>((ref) {
  final sessao = ref.read(controladorSessaoProvider.notifier);
  final dio = criarClienteHttp(
    urlBase: Ambiente.urlBaseApi,
    tokenAtual: sessao.tokenVigente,
    idioma: _idiomaDoAparelho,
    aoRecusarSessao: sessao.expirar,
  );
  ref.onDispose(dio.close);
  return dio;
});

/// O backend traduz mensagens para `pt` e `en`; qualquer outro idioma recebe `pt`.
String _idiomaDoAparelho() => PlatformDispatcher.instance.locale.languageCode == 'en' ? 'en' : 'pt';
