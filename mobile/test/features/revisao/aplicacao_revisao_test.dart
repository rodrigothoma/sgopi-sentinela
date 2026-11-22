import 'package:flutter_test/flutter_test.dart';
import 'package:sgopi_mobile/features/ocorrencias/domain/enums.dart';
import 'package:sgopi_mobile/features/revisao/application/dependencias.dart';
import 'package:sgopi_mobile/features/revisao/domain/decisao_revisao.dart';

import '../../fakes/container.dart';

void main() {
  test('justificativa curta não chega ao backend', () async {
    final d = Dubles();
    final caso = d.container().read(decidirRevisaoProvider);
    expect(() => caso.executar('oc-1', const Devolver('curta')), throwsA(isA<DecisaoInvalida>()));
    expect(d.revisao.decisoes, isEmpty);
  });

  test('decisão válida é enviada e devolve a ocorrência atualizada', () async {
    final d = Dubles();
    final caso = d.container().read(decidirRevisaoProvider);
    final o = await caso.executar('oc-1', const Devolver('Falta qualificar a testemunha.'));
    expect(o.status, StatusOcorrencia.emCorrecao);
    expect(d.revisao.decisoes.single.$2, isA<Devolver>());
  });
}
