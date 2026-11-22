import 'dart:convert';

import 'package:dio/dio.dart';

import '../dominio/falha.dart';

const _tipoPorStatus = <int, TipoFalha>{
  401: TipoFalha.naoAutenticado,
  403: TipoFalha.acessoNegado,
  404: TipoFalha.naoEncontrado,
  409: TipoFalha.conflito,
  422: TipoFalha.validacao,
  429: TipoFalha.muitasTentativas,
};

const _semResposta = {
  DioExceptionType.connectionTimeout,
  DioExceptionType.sendTimeout,
  DioExceptionType.receiveTimeout,
  DioExceptionType.connectionError,
};

/// Converte o erro do Dio na [Falha] do app, lendo o corpo padrão do backend
/// `{detail, code, request_id, extra?}` (`adapters/inbound/http/erros.py`).
Falha falhaDeErroHttp(DioException erro) {
  final resposta = erro.response;
  if (resposta == null) {
    final tipo = _semResposta.contains(erro.type) ? TipoFalha.semConexao : TipoFalha.desconhecida;
    return Falha(tipo);
  }
  final status = resposta.statusCode ?? 0;
  final corpo = _corpoJson(resposta.data);
  final extra = corpo?['extra'];
  return Falha(
    _tipoPorStatus[status] ?? (status >= 500 ? TipoFalha.servidor : TipoFalha.desconhecida),
    detalhe: corpo?['detail'] is String ? corpo!['detail'] as String : null,
    codigo: corpo?['code'] as String?,
    requestId: (corpo?['request_id'] as String?) ?? resposta.headers.value('x-request-id'),
    extra: extra is Map<String, dynamic> ? extra : const {},
  );
}

/// Respostas pedidas como bytes (download de evidência) trazem o corpo do erro sem decodificar.
Map<String, dynamic>? _corpoJson(Object? dados) {
  Object? json = dados;
  if (dados is List<int>) {
    try {
      json = jsonDecode(utf8.decode(dados));
    } on FormatException {
      return null;
    }
  }
  return json is Map<String, dynamic> ? json : null;
}

/// Executa uma chamada HTTP trocando `DioException` por [Falha], para que nenhuma
/// camada acima de `data/` conheça o Dio.
Future<T> comFalhasTraduzidas<T>(Future<T> Function() chamada) async {
  try {
    return await chamada();
  } on DioException catch (erro) {
    throw falhaDeErroHttp(erro);
  }
}
