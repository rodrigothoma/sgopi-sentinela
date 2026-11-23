import 'package:flutter_test/flutter_test.dart';
import 'package:sgopi_mobile/features/ocorrencias/domain/enums.dart';
import 'package:sgopi_mobile/features/revisao/data/repositorio_revisao_http.dart';
import 'package:sgopi_mobile/features/revisao/domain/decisao_revisao.dart';

import '../../fakes/adaptador_http_fake.dart';
import '../../fakes/exemplos.dart';

void main() {
  late AdaptadorHttpFake adaptador;
  late RepositorioRevisaoHttp repositorio;

  setUp(() {
    adaptador = AdaptadorHttpFake();
    repositorio = RepositorioRevisaoHttp(dioDeTeste(adaptador));
  });

  test('validar sem despacho envia corpo vazio', () async {
    adaptador.responder(RespostaFake(200, detalheJson(status: 'VALIDADA')));
    final o = await repositorio.decidir('oc-1', const Validar(despacho: '  '));
    expect(adaptador.ultima.path, '/v1/ocorrencias/oc-1/validar');
    expect(adaptador.ultima.data, <String, Object?>{});
    expect(o.status, StatusOcorrencia.validada);
  });

  test('devolver e rejeitar enviam a justificativa aparada', () async {
    adaptador
      ..responder(RespostaFake(200, detalheJson(status: 'EM_CORRECAO')))
      ..responder(RespostaFake(200, detalheJson(status: 'REJEITADA')));
    await repositorio.decidir('oc-1', const Devolver('  Falta qualificar a testemunha.  '));
    expect(adaptador.ultima.path, '/v1/ocorrencias/oc-1/devolver');
    expect(adaptador.ultima.data, {'justificativa': 'Falta qualificar a testemunha.'});
    await repositorio.decidir('oc-1', const Rejeitar('Fato não constitui crime.'));
    expect(adaptador.ultima.path, '/v1/ocorrencias/oc-1/rejeitar');
  });
}
