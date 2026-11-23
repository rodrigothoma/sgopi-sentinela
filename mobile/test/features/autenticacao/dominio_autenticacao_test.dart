import 'package:flutter_test/flutter_test.dart';
import 'package:sgopi_mobile/features/autenticacao/domain/papel.dart';
import 'package:sgopi_mobile/features/autenticacao/domain/permissao.dart';

import '../../fakes/exemplos.dart';

void main() {
  group('Sessao', () {
    test('vale até o instante de expiração, exclusive', () {
      final sessao = sessaoDe(Papel.agente, expiraEm: agora);
      expect(sessao.expiradaEm(agora.subtract(const Duration(seconds: 1))), isFalse);
      expect(sessao.expiradaEm(agora), isTrue);
    });
  });

  group('Papel', () {
    test('converte os códigos do backend', () {
      expect(Papel.deCodigo('OPERADOR_CENTRAL'), Papel.operadorCentral);
    });

    test('código desconhecido é quebra de contrato', () {
      expect(() => Papel.deCodigo('ADMIN'), throwsFormatException);
    });
  });

  group('Permissao', () {
    test('registrar é exclusivo do Agente e revisar do Delegado', () {
      expect(Papel.agente.pode(Permissao.registrarOcorrencia), isTrue);
      expect(Papel.delegado.pode(Permissao.registrarOcorrencia), isFalse);
      expect(Papel.delegado.pode(Permissao.revisarOcorrencia), isTrue);
      expect(Papel.supervisor.pode(Permissao.revisarOcorrencia), isFalse);
    });
  });
}
