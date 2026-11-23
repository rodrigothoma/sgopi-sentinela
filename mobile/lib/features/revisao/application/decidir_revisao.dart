import '../../ocorrencias/domain/ocorrencia.dart';
import '../domain/decisao_revisao.dart';
import '../domain/portas.dart';

/// UC04 (RF04): o Delegado valida, devolve para correção ou rejeita.
class DecidirRevisao {
  DecidirRevisao(this._repositorio);

  final RepositorioRevisao _repositorio;

  /// Lança [DecisaoInvalida] sem chamar o backend quando falta justificativa.
  Future<OcorrenciaDetalhe> executar(String ocorrenciaId, DecisaoRevisao decisao) {
    final erros = decisao.validar();
    if (erros.isNotEmpty) throw DecisaoInvalida(erros);
    return _repositorio.decidir(ocorrenciaId, decisao);
  }
}
