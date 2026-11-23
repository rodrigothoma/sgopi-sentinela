import '../../../core/dominio/enum_api.dart';

/// Papéis do RBAC, com os códigos exatos de `domain/usuario/entity.py` (enum `Papel`).
enum Papel implements EnumApi {
  agente('AGENTE'),
  delegado('DELEGADO'),
  operadorCentral('OPERADOR_CENTRAL'),
  supervisor('SUPERVISOR'),
  perito('PERITO'),
  escrivao('ESCRIVAO'),
  cidadao('CIDADAO');

  const Papel(this.codigo);

  @override
  final String codigo;

  static Papel deCodigo(String codigo) => enumDeCodigo(values, codigo);
}
