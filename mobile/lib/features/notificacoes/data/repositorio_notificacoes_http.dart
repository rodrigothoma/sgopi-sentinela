import 'package:dio/dio.dart';

import '../../../core/http/falhas_http.dart';
import '../../../core/http/json.dart';
import '../domain/notificacao.dart';
import '../domain/portas.dart';
import 'notificacao_mapper.dart';

const _base = '/v1/notificacoes';

final class RepositorioNotificacoesHttp implements RepositorioNotificacoes {
  RepositorioNotificacoesHttp(this._http);

  final Dio _http;

  @override
  Future<LoteNotificacoes> listar({required int limite, required int deslocamento}) =>
      comFalhasTraduzidas(() async {
        final resposta = await _http.get<Json>(
          _base,
          queryParameters: {'limit': limite, 'offset': deslocamento},
        );
        return NotificacaoMapper.loteDeJson(resposta.data!);
      });

  @override
  Future<int> contarNaoLidas() => comFalhasTraduzidas(() async {
    final resposta = await _http.get<Json>('$_base/resumo');
    return campo<int>(resposta.data!, 'nao_lidas');
  });

  @override
  Future<void> marcarLida(String notificacaoId) =>
      comFalhasTraduzidas(() => _http.patch<Json>('$_base/$notificacaoId/lida'));

  @override
  Future<void> marcarTodasLidas() =>
      comFalhasTraduzidas(() => _http.post<Json>('$_base/marcar-todas-lidas'));
}
