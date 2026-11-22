import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sgopi_mobile/core/dominio/falha.dart';
import 'package:sgopi_mobile/core/http/cliente_http.dart';
import 'package:sgopi_mobile/core/http/falhas_http.dart';

import '../fakes/adaptador_http_fake.dart';

void main() {
  group('falhaDeErroHttp lê o corpo padrão do backend', () {
    Future<Falha> falhaPara(RespostaFake resposta) async {
      final dio = dioDeTeste(AdaptadorHttpFake([resposta]));
      try {
        await dio.get<Object>('/x');
      } on DioException catch (erro) {
        return falhaDeErroHttp(erro);
      }
      fail('a requisição deveria falhar');
    }

    test('422 com detail, code, request_id', () async {
      final falha = await falhaPara(
        const RespostaFake(422, {
          'detail': 'A descrição deve ter ao menos 20 caracteres.',
          'code': 'ocorrencia.descricao_curta',
          'request_id': '0123456789abcdef',
          'extra': {'minimo': 20},
        }),
      );
      expect(falha.tipo, TipoFalha.validacao);
      expect(falha.codigo, 'ocorrencia.descricao_curta');
      expect(falha.referencia, '01234567');
      expect(falha.extra['minimo'], 20);
    });

    test('429 expõe o tempo de bloqueio', () async {
      final falha = await falhaPara(
        const RespostaFake(429, {
          'detail': 'Muitas tentativas.',
          'code': 'auth.muitas_tentativas',
          'request_id': 'r',
          'extra': {'retry_after_segundos': 125},
        }),
      );
      expect(falha.tipo, TipoFalha.muitasTentativas);
      expect(falha.aguardarPor, const Duration(seconds: 125));
    });

    test('5xx sem corpo vira falha de servidor com request id do cabeçalho', () async {
      final falha = await falhaPara(
        const RespostaFake(503, null, {
          'x-request-id': ['req-cabecalho'],
        }),
      );
      expect(falha.tipo, TipoFalha.servidor);
      expect(falha.requestId, 'req-cabecalho');
    });

    test('sem resposta (rede) vira semConexao', () {
      final erro = DioException.connectionError(
        requestOptions: RequestOptions(path: '/x'),
        reason: 'recusada',
      );
      expect(falhaDeErroHttp(erro).tipo, TipoFalha.semConexao);
    });
  });

  group('criarClienteHttp', () {
    late AdaptadorHttpFake adaptador;
    late int recusas;

    Dio cliente({String? token}) => criarClienteHttp(
      urlBase: 'http://api.teste',
      tokenAtual: () => token,
      idioma: () => 'en',
      aoRecusarSessao: () => recusas++,
      adaptador: adaptador,
    );

    setUp(() {
      adaptador = AdaptadorHttpFake();
      recusas = 0;
    });

    test('envia Bearer e Accept-Language', () async {
      adaptador.responder(const RespostaFake(200, {}));
      await cliente(token: 'jwt').get<Object>('/v1/ocorrencias');
      expect(adaptador.ultima.headers['Authorization'], 'Bearer jwt');
      expect(adaptador.ultima.headers['Accept-Language'], 'en');
    });

    test('401 em requisição autenticada encerra a sessão', () async {
      adaptador.responder(const RespostaFake(401, {'detail': 'x', 'code': 'auth.token_invalido'}));
      await expectLater(
        cliente(token: 'jwt').get<Object>('/v1/ocorrencias'),
        throwsA(isA<DioException>()),
      );
      expect(recusas, 1);
    });

    test('401 no login (sem token) não é sessão expirada', () async {
      adaptador.responder(
        const RespostaFake(401, {'detail': 'x', 'code': 'auth.credenciais_invalidas'}),
      );
      await expectLater(cliente().post<Object>('/v1/auth/login'), throwsA(isA<DioException>()));
      expect(recusas, 0);
    });
  });
}
