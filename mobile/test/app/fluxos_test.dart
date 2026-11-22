import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:intl/date_symbol_data_local.dart';
import 'package:material_ui/material_ui.dart';
import 'package:sgopi_mobile/app/app.dart';
import 'package:sgopi_mobile/core/dominio/falha.dart';
import 'package:sgopi_mobile/features/autenticacao/domain/papel.dart';
import 'package:sgopi_mobile/features/ocorrencias/data/ocorrencia_mapper.dart';
import 'package:sgopi_mobile/features/revisao/domain/decisao_revisao.dart';

import '../fakes/container.dart';
import '../fakes/exemplos.dart';

Future<void> _abrirApp(WidgetTester tester, Dubles d) async {
  tester.platformDispatcher.localesTestValue = const [Locale('pt', 'BR')];
  addTearDown(tester.platformDispatcher.clearLocalesTestValue);
  await tester.pumpWidget(
    ProviderScope(overrides: d.substituicoes, retry: (_, _) => null, child: const AppSgopi()),
  );
  await tester.pumpAndSettle();
}

Future<void> _entrar(WidgetTester tester, String login, {String senha = 'Senha@123'}) async {
  await tester.enterText(find.byKey(const Key('login.usuario')), login);
  await tester.enterText(find.byKey(const Key('login.senha')), senha);
  await tester.tap(find.byKey(const Key('login.entrar')));
  await tester.pumpAndSettle();
}

/// Rola a lista vertical até o alvo (o ListView só constrói o que está na tela) e toca.
Future<void> _tocar(WidgetTester tester, Finder alvo) async {
  if (alvo.evaluate().isEmpty) {
    final listaVertical = find.byWidgetPredicate(
      (w) => w is Scrollable && w.axisDirection == AxisDirection.down,
    );
    await tester.scrollUntilVisible(alvo, 200, scrollable: listaVertical.last);
  }
  await tester.ensureVisible(alvo);
  await tester.pumpAndSettle();
  await tester.tap(alvo);
  await tester.pumpAndSettle();
}

void main() {
  setUpAll(initializeDateFormatting);

  testWidgets('login recusado mostra a mensagem do backend com a referência', (tester) async {
    await _abrirApp(tester, Dubles());
    await _entrar(tester, 'agente', senha: 'errada');
    expect(find.text('Credenciais inválidas. (ref. abcdef12)'), findsOneWidget);
  });

  testWidgets('papel sem fluxo no app vê o aviso para usar o sistema web', (tester) async {
    final d = Dubles()..autenticacao.usuarios['operador'] = sessaoDe(Papel.operadorCentral);
    await _abrirApp(tester, d);
    await _entrar(tester, 'operador');
    expect(find.text('Perfil sem acesso no app'), findsOneWidget);
  });

  testWidgets('Agente registra ocorrência com GPS e envolvido e recebe o protocolo', (
    tester,
  ) async {
    final d = Dubles()..autenticacao.usuarios['agente'] = sessaoDe(Papel.agente);
    await _abrirApp(tester, d);
    await _entrar(tester, 'agente');
    expect(find.text('Minhas ocorrências'), findsOneWidget);

    await _tocar(tester, find.byKey(const Key('minhas.registrar')));
    await tester.enterText(find.byKey(const Key('ocorrencia.natureza')), 'Furto');
    await tester.enterText(
      find.byKey(const Key('ocorrencia.descricao')),
      'Subtração de celular na saída do mercado.',
    );
    await tester.enterText(find.byKey(const Key('ocorrencia.localizacao')), 'Rua Andradas, 100');

    await _tocar(tester, find.byKey(const Key('ocorrencia.enviar')));
    expect(find.text('Adicione ao menos um envolvido.'), findsOneWidget);
    expect(d.ocorrencias.registradas, isEmpty);

    await _tocar(tester, find.byKey(const Key('ocorrencia.adicionarEnvolvido')));
    await tester.enterText(find.byKey(const Key('envolvido.nome')), 'Maria Silva');
    await _tocar(tester, find.byKey(const Key('envolvido.confirmar')));
    await _tocar(tester, find.byKey(const Key('ocorrencia.enviar')));

    expect(find.textContaining('Protocolo BO-2026-000999'), findsOneWidget);
    final registrada = d.ocorrencias.registradas.single;
    expect(registrada.coordenada?.latitude, -29.78);
    expect(registrada.envolvidos.single.nome, 'Maria Silva');

    await _tocar(tester, find.text('OK'));
    expect(find.text('Ocorrência'), findsOneWidget);
  });

  testWidgets('Delegado devolve da fila exigindo justificativa', (tester) async {
    final d = Dubles()..autenticacao.usuarios['delegado'] = sessaoDe(Papel.delegado);
    final pendente = OcorrenciaMapper.detalheDeJson(detalheJson());
    d.ocorrencias.ocorrencias[pendente.id] = pendente;
    await _abrirApp(tester, d);
    await _entrar(tester, 'delegado');

    expect(find.text('Fila de revisão'), findsOneWidget);
    await _tocar(tester, find.text('BO-2026-000123'));
    await _tocar(tester, find.byKey(const Key('revisao.devolver')));

    await tester.enterText(find.byKey(const Key('decisao.texto')), 'curta');
    await _tocar(tester, find.byKey(const Key('decisao.confirmar')));
    expect(find.textContaining('ao menos 10 caracteres'), findsOneWidget);
    expect(d.revisao.decisoes, isEmpty);

    await tester.enterText(
      find.byKey(const Key('decisao.texto')),
      'Falta qualificar a testemunha.',
    );
    await _tocar(tester, find.byKey(const Key('decisao.confirmar')));
    expect(d.revisao.decisoes.single.$2, isA<Devolver>());
    expect(find.text('Ocorrência devolvida ao Agente.'), findsOneWidget);
    expect(find.text('Fila de revisão'), findsOneWidget);
  });

  testWidgets('Delegado abre a foto da evidência durante a revisão', (tester) async {
    final d = Dubles()..autenticacao.usuarios['delegado'] = sessaoDe(Papel.delegado);
    final pendente = OcorrenciaMapper.detalheDeJson(detalheJson(evidencias: 1));
    d.ocorrencias.ocorrencias[pendente.id] = pendente;
    await _abrirApp(tester, d);
    await _entrar(tester, 'delegado');
    await _tocar(tester, find.text('BO-2026-000123'));

    await _tocar(tester, find.byKey(const Key('evidencia.ev-0')));
    expect(d.ocorrencias.downloads.single, (pendente.id, 'ev-0'));
    expect(find.byKey(const Key('evidencia.imagem')), findsOneWidget);

    await _tocar(tester, find.byType(CloseButton));
    expect(find.byKey(const Key('revisao.validar')), findsOneWidget);
  });

  testWidgets('evidência adulterada mostra o erro do backend e permite tentar de novo', (
    tester,
  ) async {
    final d = Dubles()..autenticacao.usuarios['delegado'] = sessaoDe(Papel.delegado);
    final pendente = OcorrenciaMapper.detalheDeJson(detalheJson(evidencias: 1));
    d.ocorrencias
      ..ocorrencias[pendente.id] = pendente
      ..conteudoEvidencia = const Falha(
        TipoFalha.conflito,
        detalhe: 'Integridade da evidência comprometida',
        requestId: 'abcdef1234567890',
      );
    await _abrirApp(tester, d);
    await _entrar(tester, 'delegado');
    await _tocar(tester, find.text('BO-2026-000123'));
    await _tocar(tester, find.byKey(const Key('evidencia.ev-0')));

    expect(find.textContaining('Integridade da evidência comprometida'), findsOneWidget);
    d.ocorrencias.conteudoEvidencia = pngMinimo;
    await _tocar(tester, find.text('Tentar novamente'));
    expect(find.byKey(const Key('evidencia.imagem')), findsOneWidget);
    expect(d.ocorrencias.downloads, hasLength(2));
  });
}
