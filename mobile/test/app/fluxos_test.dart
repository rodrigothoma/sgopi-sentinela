import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:intl/date_symbol_data_local.dart';
import 'package:material_ui/material_ui.dart';
import 'package:sgopi_mobile/app/app.dart';
import 'package:sgopi_mobile/core/dominio/falha.dart';
import 'package:sgopi_mobile/features/autenticacao/domain/papel.dart';
import 'package:sgopi_mobile/features/ocorrencias/data/ocorrencia_mapper.dart';
import 'package:sgopi_mobile/features/preferencias/domain/preferencias.dart';
import 'package:sgopi_mobile/features/revisao/domain/decisao_revisao.dart';

import '../fakes/container.dart';
import '../fakes/exemplos.dart';

Future<void> _abrirApp(WidgetTester tester, Dubles d) async {
  tester.platformDispatcher
    ..localesTestValue = const [Locale('pt', 'BR')]
    // Texto ampliado (acessibilidade): estouros de layout falham o teste.
    ..textScaleFactorTestValue = 1.3;
  // Tela de celular comum (360×780 dp), em vez dos 800×600 padrão do teste.
  tester.view
    ..physicalSize = const Size(1080, 2340)
    ..devicePixelRatio = 3;
  addTearDown(tester.platformDispatcher.clearAllTestValues);
  addTearDown(tester.view.reset);
  await tester.pumpWidget(
    ProviderScope(overrides: d.substituicoes, retry: (_, _) => null, child: const AppSgopi()),
  );
  await tester.pumpAndSettle();
}

Future<void> _entrar(WidgetTester tester, String login, {String senha = 'Senha@123'}) async {
  await tester.enterText(find.byKey(const Key('login.usuario')), login);
  await tester.enterText(find.byKey(const Key('login.senha')), senha);
  await _tocar(tester, find.byKey(const Key('login.entrar')));
}

/// Rola a lista vertical até o alvo (o ListView só constrói o que está na tela) e toca.
Future<void> _tocar(WidgetTester tester, Finder alvo) async {
  if (alvo.evaluate().isEmpty) {
    // A maior lista vertical da tela (campos de texto também têm Scrollable interno).
    final listas =
        find
            .byWidgetPredicate((w) => w is Scrollable && w.axisDirection == AxisDirection.down)
            .evaluate()
            .toList()
          ..sort((a, b) => b.size!.height.compareTo(a.size!.height));
    await tester.scrollUntilVisible(
      alvo,
      200,
      scrollable: find.byElementPredicate((e) => e == listas.first),
    );
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
    expect(find.textContaining('Adicione ao menos um envolvido.'), findsWidgets);
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

  testWidgets('barra inferior mostra as abas do papel e o selo de não lidas', (tester) async {
    final d = Dubles()..autenticacao.usuarios['agente'] = sessaoDe(Papel.agente);
    d.notificacoes.itens.addAll([notificacaoDe(id: 'a'), notificacaoDe(id: 'b')]);
    await _abrirApp(tester, d);
    await _entrar(tester, 'agente');

    expect(find.byKey(const Key('aba.ocorrencias')), findsOneWidget);
    expect(find.byKey(const Key('aba.notificacoes')), findsOneWidget);
    expect(find.byKey(const Key('aba.ajustes')), findsOneWidget);
    expect(find.byKey(const Key('aba.revisao')), findsNothing);
    expect(
      find.descendant(of: find.byKey(const Key('aba.notificacoes')), matching: find.text('2')),
      findsOneWidget,
    );
  });

  testWidgets('tocar na notificação marca como lida e abre a revisão da ocorrência', (
    tester,
  ) async {
    final d = Dubles()..autenticacao.usuarios['delegado'] = sessaoDe(Papel.delegado);
    final pendente = OcorrenciaMapper.detalheDeJson(detalheJson());
    d.ocorrencias.ocorrencias[pendente.id] = pendente;
    d.notificacoes.itens.add(notificacaoDe(ocorrenciaId: pendente.id, tipo: 'NOVA_OCORRENCIA'));
    await _abrirApp(tester, d);
    await _entrar(tester, 'delegado');

    await _tocar(tester, find.byKey(const Key('aba.notificacoes')));
    expect(find.text('há 5 min', findRichText: true), findsNothing);
    expect(find.textContaining('há 5 min'), findsOneWidget);
    await _tocar(tester, find.byKey(const Key('notificacao.n-1')));

    expect(d.notificacoes.marcadas, ['n-1']);
    expect(find.byKey(const Key('revisao.validar')), findsOneWidget);
    expect(find.byKey(const Key('aba.notificacoes')), findsNothing, reason: 'fluxo sem a barra');

    // `pageBack` do flutter_test não conhece o BackButton do pacote material_ui.
    await _tocar(tester, find.byType(BackButton));
    expect(find.byKey(const Key('notificacao.naoLida')), findsNothing);
    expect(find.byKey(const Key('aba.notificacoes')), findsOneWidget);
  });

  testWidgets('ajustes trocam tema e idioma na hora e guardam a escolha', (tester) async {
    final d = Dubles()..autenticacao.usuarios['agente'] = sessaoDe(Papel.agente);
    await _abrirApp(tester, d);
    await _entrar(tester, 'agente');
    await _tocar(tester, find.byKey(const Key('aba.ajustes')));
    expect(find.text('Agente · AGENTE'), findsOneWidget);

    await _tocar(tester, find.text('Escuro'));
    expect(tester.widget<MaterialApp>(find.byType(MaterialApp)).themeMode, ThemeMode.dark);

    await _tocar(tester, find.byKey(const Key('ajustes.idioma.en')));
    expect(find.text('Language'), findsOneWidget);
    expect(find.text('Settings'), findsWidgets);
    expect(find.text('Notifications'), findsOneWidget);
    expect(
      d.preferencias.preferencias,
      const Preferencias(tema: ModoTema.escuro, idioma: IdiomaApp.en),
    );
  });

  testWidgets('sair pelos ajustes pede confirmação e volta ao login', (tester) async {
    final d = Dubles()..autenticacao.usuarios['delegado'] = sessaoDe(Papel.delegado);
    await _abrirApp(tester, d);
    await _entrar(tester, 'delegado');
    await _tocar(tester, find.byKey(const Key('aba.ajustes')));

    await _tocar(tester, find.byKey(const Key('ajustes.sair')));
    await _tocar(tester, find.byKey(const Key('ajustes.confirmarSair')));
    expect(find.byKey(const Key('login.entrar')), findsOneWidget);
    expect(d.armazenamento.sessao, isNull);
  });

  testWidgets('o login já permite escolher o idioma', (tester) async {
    await _abrirApp(tester, Dubles());
    await _tocar(tester, find.byKey(const Key('preferencias.idioma')));
    await _tocar(tester, find.text('English').last);
    expect(find.text('Sign in'), findsWidgets);
  });
}
