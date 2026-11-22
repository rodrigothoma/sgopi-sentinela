import 'package:flutter_test/flutter_test.dart';
import 'package:sgopi_mobile/core/dominio/falha.dart';
import 'package:sgopi_mobile/features/notificacoes/application/notificacoes.dart';
import 'package:sgopi_mobile/features/notificacoes/data/notificacao_mapper.dart';
import 'package:sgopi_mobile/features/notificacoes/data/repositorio_notificacoes_http.dart';

import '../../fakes/adaptador_http_fake.dart';
import '../../fakes/container.dart';
import '../../fakes/exemplos.dart';

Map<String, Object?> _json({String id = 'n-1', String? link}) => {
  'id': id,
  'usuario_id': 'u-1',
  'papel_destinatario': null,
  'departamento_destinatario': null,
  'titulo': 'Ocorrência devolvida',
  'mensagem': 'Falta qualificar a testemunha.',
  'tipo': 'REVISAO_OCORRENCIA',
  'prioridade': 'ALTA',
  'link': link,
  'lida': false,
  'lida_em': null,
  'criada_em': '2026-11-22T14:55:00+00:00',
};

void main() {
  group('Notificacao', () {
    test('lê a ocorrência citada no link do web', () {
      expect(notificacaoDe(ocorrenciaId: 'oc-9').ocorrenciaVinculada, 'oc-9');
      expect(notificacaoDe(ocorrenciaId: null).ocorrenciaVinculada, isNull);
      final semParametro = NotificacaoMapper.deJson(_json(link: '/medidas'));
      expect(semParametro.ocorrenciaVinculada, isNull);
    });
  });

  group('RepositorioNotificacoesHttp', () {
    late AdaptadorHttpFake adaptador;
    late RepositorioNotificacoesHttp repositorio;

    setUp(() {
      adaptador = AdaptadorHttpFake();
      repositorio = RepositorioNotificacoesHttp(dioDeTeste(adaptador));
    });

    test('lista com paginação e lê o contador de não lidas', () async {
      adaptador.responder(
        RespostaFake(200, {
          'itens': [_json(link: '/fila?ocorrencia=oc-1')],
          'total': 1,
          'nao_lidas': 4,
          'limit': 30,
          'offset': 0,
        }),
      );
      final lote = await repositorio.listar(limite: 30, deslocamento: 0);
      expect(adaptador.ultima.path, '/v1/notificacoes');
      expect(adaptador.ultima.queryParameters, {'limit': 30, 'offset': 0});
      expect(lote.naoLidas, 4);
      expect(lote.itens.single.importante, isTrue);
      expect(lote.itens.single.criadaEm, DateTime.utc(2026, 11, 22, 14, 55));
    });

    test('resumo, marcar uma e marcar todas usam as rotas do backend', () async {
      adaptador
        ..responder(const RespostaFake(200, {'nao_lidas': 2}))
        ..responder(RespostaFake(200, _json()))
        ..responder(const RespostaFake(200, {'atualizadas': 2}));
      expect(await repositorio.contarNaoLidas(), 2);
      expect(adaptador.ultima.path, '/v1/notificacoes/resumo');
      await repositorio.marcarLida('n-1');
      expect(
        (adaptador.ultima.method, adaptador.ultima.path),
        ('PATCH', '/v1/notificacoes/n-1/lida'),
      );
      await repositorio.marcarTodasLidas();
      expect(
        (adaptador.ultima.method, adaptador.ultima.path),
        ('POST', '/v1/notificacoes/marcar-todas-lidas'),
      );
    });
  });

  group('ListaNotificacoes', () {
    test('pede a próxima página enquanto a última vier cheia', () async {
      final d = Dubles();
      d.notificacoes.itens.addAll([
        for (var i = 0; i < tamanhoPaginaNotificacoes + 5; i++) notificacaoDe(id: 'n-$i'),
      ]);
      final container = d.container();
      final lista = container.listen(listaNotificacoesProvider, (_, _) {});
      await container.read(listaNotificacoesProvider.future);
      expect(lista.read().value!.temMais, isTrue);

      await container.read(listaNotificacoesProvider.notifier).carregarMais();
      final estado = lista.read().value!;
      expect(estado.itens, hasLength(tamanhoPaginaNotificacoes + 5));
      expect(estado.temMais, isFalse);
      expect(d.notificacoes.consultas.last, (tamanhoPaginaNotificacoes, tamanhoPaginaNotificacoes));
    });

    test('marcar como lida atualiza a lista e o contador na hora', () async {
      final d = Dubles();
      d.notificacoes.itens.addAll([notificacaoDe(id: 'a'), notificacaoDe(id: 'b')]);
      final container = d.container();
      container
        ..listen(listaNotificacoesProvider, (_, _) {})
        ..listen(naoLidasProvider, (_, _) {});
      await container.read(listaNotificacoesProvider.future);
      expect(await container.read(naoLidasProvider.future), 2);

      final primeira = container.read(listaNotificacoesProvider).value!.itens.first;
      await container.read(listaNotificacoesProvider.notifier).marcarLida(primeira);
      expect(container.read(listaNotificacoesProvider).value!.itens.first.lida, isTrue);
      expect(container.read(naoLidasProvider).value, 1);
      expect(d.notificacoes.marcadas, ['a']);
    });

    test('se o backend recusa, a marcação é desfeita', () async {
      final d = Dubles()
        ..notificacoes.itens.add(notificacaoDe())
        ..notificacoes.falhaAoMarcar = const Falha(TipoFalha.semConexao);
      final container = d.container();
      container.listen(listaNotificacoesProvider, (_, _) {});
      await container.read(listaNotificacoesProvider.future);
      final notificacao = container.read(listaNotificacoesProvider).value!.itens.single;

      await expectLater(
        container.read(listaNotificacoesProvider.notifier).marcarLida(notificacao),
        throwsA(isA<Falha>()),
      );
      expect(container.read(listaNotificacoesProvider).value!.itens.single.lida, isFalse);
    });

    test('marcar todas zera as pendências', () async {
      final d = Dubles();
      d.notificacoes.itens.addAll([notificacaoDe(id: 'a'), notificacaoDe(id: 'b', lida: true)]);
      final container = d.container();
      container.listen(listaNotificacoesProvider, (_, _) {});
      await container.read(listaNotificacoesProvider.future);

      await container.read(listaNotificacoesProvider.notifier).marcarTodasLidas();
      expect(container.read(listaNotificacoesProvider).value!.itens.every((n) => n.lida), isTrue);
      expect(d.notificacoes.marcarTodasChamadas, 1);
      expect(await container.read(naoLidasProvider.future), 0);
    });
  });
}
