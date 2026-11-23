import '../../../core/l10n/gerado/textos.dart';
import '../domain/papel.dart';

extension RotuloPapel on Papel {
  String rotulo(Textos t) => switch (this) {
    Papel.agente => t.papelAgente,
    Papel.delegado => t.papelDelegado,
    Papel.operadorCentral => t.papelOperadorCentral,
    Papel.supervisor => t.papelSupervisor,
    Papel.perito => t.papelPerito,
    Papel.escrivao => t.papelEscrivao,
    Papel.cidadao => t.papelCidadao,
  };
}
