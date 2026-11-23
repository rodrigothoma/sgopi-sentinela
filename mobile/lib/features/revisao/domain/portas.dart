import '../../ocorrencias/domain/ocorrencia.dart';
import 'decisao_revisao.dart';

/// Porta de saída para as decisões do Delegado (`/validar`, `/devolver`, `/rejeitar`).
abstract interface class RepositorioRevisao {
  Future<OcorrenciaDetalhe> decidir(String ocorrenciaId, DecisaoRevisao decisao);
}
