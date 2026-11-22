import 'package:flutter_test/flutter_test.dart';
import 'package:riverpod/riverpod.dart';
import 'package:sgopi_mobile/app/guarda_rotas.dart';
import 'package:sgopi_mobile/core/apresentacao/rotas.dart';
import 'package:sgopi_mobile/features/autenticacao/application/controlador_sessao.dart';
import 'package:sgopi_mobile/features/autenticacao/domain/papel.dart';

import '../fakes/exemplos.dart';

AsyncValue<EstadoSessao> _logado(Papel papel) => AsyncData(ComSessao(sessaoDe(papel)));

void main() {
  test('enquanto restaura a sessão, fica na abertura', () {
    expect(redirecionar(const AsyncLoading(), Rotas.minhasOcorrencias), Rotas.abertura);
    expect(redirecionar(const AsyncLoading(), Rotas.abertura), isNull);
  });

  test('sem sessão, qualquer destino vai para o login', () {
    const semSessao = AsyncData<EstadoSessao>(SemSessao());
    expect(redirecionar(semSessao, Rotas.filaRevisao), Rotas.login);
    expect(redirecionar(semSessao, Rotas.login), isNull);
  });

  test('cada papel fica no próprio fluxo', () {
    expect(redirecionar(_logado(Papel.agente), Rotas.login), Rotas.minhasOcorrencias);
    expect(redirecionar(_logado(Papel.agente), Rotas.detalheOcorrencia('1')), isNull);
    expect(redirecionar(_logado(Papel.agente), Rotas.filaRevisao), Rotas.minhasOcorrencias);
    expect(redirecionar(_logado(Papel.delegado), Rotas.revisarOcorrencia('1')), isNull);
    expect(redirecionar(_logado(Papel.delegado), Rotas.registrarOcorrencia), Rotas.filaRevisao);
    expect(redirecionar(_logado(Papel.operadorCentral), Rotas.abertura), Rotas.semAcesso);
  });
}
