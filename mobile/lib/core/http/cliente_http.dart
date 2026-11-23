import 'package:dio/dio.dart';

const _tempoLimiteConexao = Duration(seconds: 10);
const _tempoLimiteResposta = Duration(seconds: 30);

/// Cria o cliente HTTP único do app, com os mesmos cabeçalhos do frontend web.
///
/// - `Authorization: Bearer <jwt>` quando há sessão ([tokenAtual]);
/// - `Accept-Language` para o backend devolver `detail` já traduzido;
/// - 401 em requisição autenticada chama [aoRecusarSessao] (token vencido,
///   usuário desativado ou papel alterado no backend).
Dio criarClienteHttp({
  required String urlBase,
  required String? Function() tokenAtual,
  required String Function() idioma,
  required void Function() aoRecusarSessao,
  HttpClientAdapter? adaptador,
}) {
  final dio = Dio(
    BaseOptions(
      baseUrl: urlBase,
      connectTimeout: _tempoLimiteConexao,
      receiveTimeout: _tempoLimiteResposta,
      listFormat: ListFormat.multi,
      responseType: ResponseType.json,
    ),
  );
  if (adaptador != null) dio.httpClientAdapter = adaptador;
  dio.interceptors.add(_InterceptadorSessao(tokenAtual, idioma, aoRecusarSessao));
  return dio;
}

final class _InterceptadorSessao extends Interceptor {
  _InterceptadorSessao(this._tokenAtual, this._idioma, this._aoRecusarSessao);

  final String? Function() _tokenAtual;
  final String Function() _idioma;
  final void Function() _aoRecusarSessao;

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    options.headers['Accept-Language'] = _idioma();
    final token = _tokenAtual();
    if (token != null) options.headers['Authorization'] = 'Bearer $token';
    handler.next(options);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    final autenticada = err.requestOptions.headers.containsKey('Authorization');
    if (err.response?.statusCode == 401 && autenticada) _aoRecusarSessao();
    handler.next(err);
  }
}
