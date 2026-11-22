import 'package:flutter_test/flutter_test.dart';
import 'package:sgopi_mobile/features/revisao/domain/decisao_revisao.dart';

void main() {
  test('validar dispensa justificativa', () {
    expect(const Validar().validar(), isEmpty);
  });

  test('devolver e rejeitar exigem justificativa com o mínimo do backend', () {
    final curta = ' ${'x' * (tamanhoMinimoJustificativa - 1)} ';
    final suficiente = 'x' * tamanhoMinimoJustificativa;
    expect(Devolver(curta).validar(), {ErroDecisao.justificativaCurta});
    expect(Rejeitar(curta).validar(), {ErroDecisao.justificativaCurta});
    expect(Devolver(suficiente).validar(), isEmpty);
  });
}
