import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:sgopi_mobile/core/dominio/falha.dart';
import 'package:sgopi_mobile/features/ocorrencias/data/ocorrencia_mapper.dart';
import 'package:sgopi_mobile/features/ocorrencias/data/repositorio_ocorrencias_http.dart';
import 'package:sgopi_mobile/features/ocorrencias/domain/arquivo_evidencia.dart';
import 'package:sgopi_mobile/features/ocorrencias/domain/enums.dart';
import 'package:sgopi_mobile/features/ocorrencias/domain/ocorrencia.dart';

import '../../fakes/adaptador_http_fake.dart';
import '../../fakes/exemplos.dart';

void main() {
  group('OcorrenciaMapper', () {
    test('lê o OcorrenciaDetalheSchema do backend', () {
      final o = OcorrenciaMapper.detalheDeJson(detalheJson(evidencias: 2));
      expect(o.numeroProtocolo, 'BO-2026-000123');
      expect(o.status, StatusOcorrencia.aguardandoRevisao);
      expect(o.prioridade, PrioridadeOcorrencia.alta);
      expect(o.dataHoraFato, DateTime.utc(2026, 11, 22, 14));
      expect(o.envolvidos.single.tipo, TipoEnvolvido.vitima);
      expect(o.evidencias, hasLength(2));
      expect(o.historico.single.de, isNull);
    });

    test('registro envia datas em UTC, campos aparados e opcionais nulos', () {
      final json = OcorrenciaMapper.registroParaJson(dadosValidos());
      expect(json['data_hora_fato'], '2026-11-22T14:00:00.000Z');
      expect(json['latitude'], -29.78);
      expect(json.containsKey('prioridade'), isFalse);
      expect((json['envolvidos'] as List).single, {
        'nome': 'Maria Silva',
        'tipo': 'VITIMA',
        'documento': null,
        'email': null,
        'telefone': null,
      });
    });

    test('correção não envia prioridade (o PUT não aceita)', () {
      final json = OcorrenciaMapper.correcaoParaJson(dadosValidos());
      expect(json.containsKey('prioridade'), isFalse);
    });
  });

  group('RepositorioOcorrenciasHttp', () {
    late AdaptadorHttpFake adaptador;
    late RepositorioOcorrenciasHttp repositorio;

    setUp(() {
      adaptador = AdaptadorHttpFake();
      repositorio = RepositorioOcorrenciasHttp(dioDeTeste(adaptador));
    });

    test('listar envia paginação, status repetido e flags', () async {
      adaptador.responder(
        RespostaFake(200, {
          'itens': [detalheJson()],
          'total': 1,
          'limit': 20,
          'offset': 0,
        }),
      );
      final pagina = await repositorio.listar(
        const FiltroOcorrencias(
          status: {StatusOcorrencia.aguardandoRevisao, StatusOcorrencia.emCorrecao},
          somenteMinhas: true,
        ),
        limite: 20,
        deslocamento: 0,
      );
      final uri = adaptador.ultima.uri;
      expect(uri.path, '/v1/ocorrencias');
      expect(
        uri.queryParametersAll['status'],
        unorderedEquals(['AGUARDANDO_REVISAO', 'EM_CORRECAO']),
      );
      expect(uri.queryParameters['somente_minhas'], 'true');
      expect(uri.queryParameters.containsKey('ordenar_por_prioridade'), isFalse);
      expect(pagina.itens.single.id, 'oc-1');
    });

    test('registrar faz POST e devolve o protocolo', () async {
      adaptador.responder(
        const RespostaFake(201, {
          'ocorrencia_id': 'oc-9',
          'numero_protocolo': 'BO-2026-000009',
          'status': 'AGUARDANDO_REVISAO',
          'criada_em': '2026-11-22T15:00:00+00:00',
          'prioridade': 'MEDIA',
        }),
      );
      final protocolo = await repositorio.registrar(dadosValidos());
      expect(adaptador.ultima.method, 'POST');
      expect(protocolo.numeroProtocolo, 'BO-2026-000009');
    });

    test('corrigir faz PUT e reenviar faz POST em /reenviar', () async {
      adaptador
        ..responder(RespostaFake(200, detalheJson(status: 'EM_CORRECAO')))
        ..responder(RespostaFake(200, detalheJson()));
      await repositorio.corrigir('oc-1', dadosValidos());
      expect((adaptador.ultima.method, adaptador.ultima.path), ('PUT', '/v1/ocorrencias/oc-1'));
      await repositorio.reenviar('oc-1');
      expect(
        (adaptador.ultima.method, adaptador.ultima.path),
        ('POST', '/v1/ocorrencias/oc-1/reenviar'),
      );
    });

    test('anexar envia multipart no campo "arquivo" com o MIME do formato', () async {
      final temporario = await File('${Directory.systemTemp.createTempSync().path}/foto.jpg')
          .writeAsBytes([0xFF, 0xD8, 0xFF, 0xE0]);
      adaptador.responder(
        const RespostaFake(201, {
          'id': 'ev-1',
          'nome_original': 'foto.jpg',
          'formato': 'jpeg',
          'tamanho': 4,
          'hash_sha256': 'abc',
          'enviada_em': '2026-11-22T15:00:00+00:00',
        }),
      );
      final evidencia = await repositorio.anexarEvidencia(
        'oc-1',
        ArquivoEvidencia(caminho: temporario.path, nome: 'foto.jpg', tamanhoBytes: 4),
      );
      expect(adaptador.ultima.path, '/v1/ocorrencias/oc-1/evidencias');
      expect(adaptador.ultimoCorpoTexto, contains('name="arquivo"; filename="foto.jpg"'));
      expect(adaptador.ultimoCorpoTexto, contains('content-type: image/jpeg'));
      expect(evidencia.id, 'ev-1');
    });

    test('baixa a evidência como bytes pela rota autorizada', () async {
      adaptador.responder(RespostaFake(200, pngMinimo));
      final bytes = await repositorio.baixarEvidencia('oc-1', 'ev-1');
      expect(adaptador.ultima.path, '/v1/ocorrencias/oc-1/evidencias/ev-1/download');
      expect(bytes, pngMinimo);
    });

    test('download com integridade divergente traz a mensagem do backend', () async {
      final corpo = utf8.encode(
        jsonEncode({
          'detail': 'Integridade da evidência comprometida',
          'code': 'evidencia.integridade_divergente',
          'request_id': 'r',
        }),
      );
      adaptador.responder(RespostaFake(409, Uint8List.fromList(corpo)));
      await expectLater(
        repositorio.baixarEvidencia('oc-1', 'ev-1'),
        throwsA(
          isA<Falha>()
              .having((f) => f.tipo, 'tipo', TipoFalha.conflito)
              .having((f) => f.detalhe, 'detalhe', 'Integridade da evidência comprometida'),
        ),
      );
    });

    test('erro do backend vira Falha', () async {
      adaptador.responder(
        const RespostaFake(404, {
          'detail': 'Não encontrada',
          'code': 'ocorrencia.nao_encontrada',
          'request_id': 'r',
        }),
      );
      await expectLater(
        repositorio.obter('x'),
        throwsA(isA<Falha>().having((f) => f.tipo, 'tipo', TipoFalha.naoEncontrado)),
      );
    });
  });
}
