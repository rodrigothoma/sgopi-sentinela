import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sgopi_mobile/core/dominio/falha.dart';
import 'package:sgopi_mobile/features/autenticacao/data/armazenamento_sessao_seguro.dart';
import 'package:sgopi_mobile/features/autenticacao/data/repositorio_autenticacao_http.dart';
import 'package:sgopi_mobile/features/autenticacao/domain/papel.dart';

import '../../fakes/adaptador_http_fake.dart';
import '../../fakes/exemplos.dart';

const _respostaLogin = {
  'access_token': 'jwt.assinado',
  'token_type': 'bearer',
  'expira_em': '2026-11-22T23:00:00+00:00',
  'usuario': {'id': 'u-1', 'nome': 'Ana Agente', 'login': 'agente', 'papel': 'AGENTE'},
};

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('RepositorioAutenticacaoHttp', () {
    test('envia JSON {login, senha} e monta a sessão', () async {
      final adaptador = AdaptadorHttpFake([const RespostaFake(200, _respostaLogin)]);
      final sessao = await RepositorioAutenticacaoHttp(dioDeTeste(adaptador))
          .entrar(login: 'agente', senha: 'Senha@123');

      expect(adaptador.ultima.method, 'POST');
      expect(adaptador.ultima.path, '/v1/auth/login');
      expect(adaptador.ultima.data, {'login': 'agente', 'senha': 'Senha@123'});
      expect(sessao.token, 'jwt.assinado');
      expect(sessao.usuario.papel, Papel.agente);
      expect(sessao.expiraEm, DateTime.utc(2026, 11, 22, 23));
    });

    test('credenciais inválidas chegam como Falha naoAutenticado', () async {
      final adaptador = AdaptadorHttpFake([
        const RespostaFake(401, {
          'detail': 'Credenciais inválidas.',
          'code': 'auth.credenciais_invalidas',
          'request_id': 'r',
        }),
      ]);
      final repositorio = RepositorioAutenticacaoHttp(dioDeTeste(adaptador));
      await expectLater(
        repositorio.entrar(login: 'agente', senha: 'errada'),
        throwsA(isA<Falha>().having((f) => f.tipo, 'tipo', TipoFalha.naoAutenticado)),
      );
    });
  });

  group('ArmazenamentoSessaoSeguro', () {
    setUp(() => FlutterSecureStorage.setMockInitialValues({}));

    test('salva e restaura a mesma sessão', () async {
      final armazenamento = ArmazenamentoSessaoSeguro(const FlutterSecureStorage());
      await armazenamento.salvar(sessaoDe(Papel.delegado));
      final restaurada = await armazenamento.carregar();
      expect(restaurada?.token, 'jwt-DELEGADO');
      expect(restaurada?.usuario.papel, Papel.delegado);
      expect(restaurada?.expiraEm, sessaoDe(Papel.delegado).expiraEm);
    });

    test('conteúdo corrompido é descartado', () async {
      FlutterSecureStorage.setMockInitialValues({'sgopi.sessao': '{nao-e-json'});
      final armazenamento = ArmazenamentoSessaoSeguro(const FlutterSecureStorage());
      expect(await armazenamento.carregar(), isNull);
      expect(await const FlutterSecureStorage().read(key: 'sgopi.sessao'), isNull);
    });
  });
}
