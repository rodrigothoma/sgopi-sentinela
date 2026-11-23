import 'package:dio/dio.dart';

import '../../../core/http/falhas_http.dart';
import '../../../core/http/json.dart';
import '../domain/portas.dart';
import '../domain/sessao.dart';
import 'sessao_mapper.dart';

final class RepositorioAutenticacaoHttp implements RepositorioAutenticacao {
  RepositorioAutenticacaoHttp(this._http);

  final Dio _http;

  @override
  Future<Sessao> entrar({required String login, required String senha}) =>
      comFalhasTraduzidas(() async {
        final resposta = await _http.post<Json>(
          '/v1/auth/login',
          data: {'login': login, 'senha': senha},
        );
        return SessaoMapper.deJson(resposta.data!);
      });
}
