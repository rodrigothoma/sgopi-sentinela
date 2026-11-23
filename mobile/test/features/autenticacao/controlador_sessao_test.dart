import 'package:flutter_test/flutter_test.dart';
import 'package:sgopi_mobile/core/dominio/falha.dart';
import 'package:sgopi_mobile/features/autenticacao/application/controlador_sessao.dart';
import 'package:sgopi_mobile/features/autenticacao/domain/papel.dart';

import '../../fakes/container.dart';
import '../../fakes/exemplos.dart';

void main() {
  late Dubles d;

  setUp(() => d = Dubles());

  Future<EstadoSessao> estadoInicial() => d.container().read(controladorSessaoProvider.future);

  test('abre sem sessão salva', () async {
    expect(await estadoInicial(), isA<SemSessao>().having((s) => s.expirou, 'expirou', isFalse));
  });

  test('restaura a sessão salva ainda válida', () async {
    d.armazenamento.sessao = sessaoDe(Papel.agente);
    expect(await estadoInicial(), isA<ComSessao>());
  });

  test('sessão salva vencida é descartada e sinalizada', () async {
    d.armazenamento.sessao = sessaoDe(Papel.agente, expiraEm: agora);
    expect(await estadoInicial(), isA<SemSessao>().having((s) => s.expirou, 'expirou', isTrue));
    expect(d.armazenamento.sessao, isNull);
  });

  test('entrar salva a sessão e apara o login', () async {
    d.autenticacao.usuarios['agente'] = sessaoDe(Papel.agente);
    final container = d.container();
    await container.read(controladorSessaoProvider.future);
    await container
        .read(controladorSessaoProvider.notifier)
        .entrar(login: ' agente ', senha: 'Senha@123');
    expect(container.read(sessaoAtualProvider)?.usuario.papel, Papel.agente);
    expect(d.armazenamento.sessao?.token, 'jwt-AGENTE');
  });

  test('credenciais inválidas lançam Falha sem mudar o estado', () async {
    final container = d.container();
    await container.read(controladorSessaoProvider.future);
    await expectLater(
      container.read(controladorSessaoProvider.notifier).entrar(login: 'x', senha: 'y'),
      throwsA(isA<Falha>()),
    );
    expect(container.read(controladorSessaoProvider).value, isA<SemSessao>());
  });

  test('sair limpa a sessão sem aviso de expiração', () async {
    d.armazenamento.sessao = sessaoDe(Papel.delegado);
    final container = d.container();
    await container.read(controladorSessaoProvider.future);
    await container.read(controladorSessaoProvider.notifier).sair();
    expect(
      container.read(controladorSessaoProvider).value,
      isA<SemSessao>().having((s) => s.expirou, 'expirou', isFalse),
    );
    expect(d.armazenamento.sessao, isNull);
  });

  test('tokenVigente expira a sessão quando o prazo passa', () async {
    d.armazenamento.sessao = sessaoDe(Papel.agente);
    final container = d.container();
    await container.read(controladorSessaoProvider.future);
    final controlador = container.read(controladorSessaoProvider.notifier);
    expect(controlador.tokenVigente(), 'jwt-AGENTE');

    d.relogio.instante = agora.add(const Duration(hours: 9));
    expect(controlador.tokenVigente(), isNull);
    await pumpEventQueue();
    expect(
      container.read(controladorSessaoProvider).value,
      isA<SemSessao>().having((s) => s.expirou, 'expirou', isTrue),
    );
  });
}
