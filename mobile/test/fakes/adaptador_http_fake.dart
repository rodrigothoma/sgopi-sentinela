import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';

/// Resposta programada para o [AdaptadorHttpFake]. Um `Uint8List` em [corpo] vai como binário.
final class RespostaFake {
  const RespostaFake(this.status, [this.corpo, this.cabecalhos = const {}]);

  final int status;
  final Object? corpo;
  final Map<String, List<String>> cabecalhos;
}

/// Substitui a rede no Dio: registra as requisições e devolve respostas programadas.
final class AdaptadorHttpFake implements HttpClientAdapter {
  AdaptadorHttpFake([List<RespostaFake>? respostas]) : _respostas = [...?respostas];

  final List<RespostaFake> _respostas;
  final List<RequestOptions> requisicoes = [];
  final List<Uint8List> corpos = [];

  void responder(RespostaFake resposta) => _respostas.add(resposta);

  RequestOptions get ultima => requisicoes.last;

  String get ultimoCorpoTexto => utf8.decode(corpos.last, allowMalformed: true);

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    requisicoes.add(options);
    corpos.add(await _ler(requestStream));
    if (_respostas.isEmpty) throw StateError('Sem resposta programada para ${options.path}');
    final resposta = _respostas.removeAt(0);
    if (resposta.corpo case final Uint8List bytes) {
      return ResponseBody.fromBytes(
        bytes,
        resposta.status,
        headers: {
          Headers.contentTypeHeader: ['application/octet-stream'],
          ...resposta.cabecalhos,
        },
      );
    }
    return ResponseBody.fromString(
      resposta.corpo == null ? '' : jsonEncode(resposta.corpo),
      resposta.status,
      headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
        ...resposta.cabecalhos,
      },
    );
  }

  static Future<Uint8List> _ler(Stream<Uint8List>? fluxo) async {
    if (fluxo == null) return Uint8List(0);
    final bytes = await fluxo.fold<List<int>>([], (acc, parte) => acc..addAll(parte));
    return Uint8List.fromList(bytes);
  }

  @override
  void close({bool force = false}) {}
}

/// Dio sem interceptores ligado ao adaptador falso, para testar os repositórios HTTP.
Dio dioDeTeste(AdaptadorHttpFake adaptador) =>
    Dio(BaseOptions(baseUrl: 'http://api.teste', listFormat: ListFormat.multi))
      ..httpClientAdapter = adaptador;
