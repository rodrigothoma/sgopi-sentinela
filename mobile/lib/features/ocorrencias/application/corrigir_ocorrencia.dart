import '../../../core/dominio/relogio.dart';
import '../domain/arquivo_evidencia.dart';
import '../domain/dados_ocorrencia.dart';
import '../domain/ocorrencia.dart';
import '../domain/portas.dart';
import 'envio_evidencias.dart';

final class ResultadoCorrecao {
  const ResultadoCorrecao(this.ocorrencia, this.evidenciasNaoEnviadas);

  final OcorrenciaDetalhe ocorrencia;
  final List<EnvioEvidenciaFalhou> evidenciasNaoEnviadas;
}

/// UC04, fluxo de correção: o Agente autor ajusta a narrativa devolvida pelo Delegado.
///
/// O reenvio à fila é um ato separado ([RepositorioOcorrencias.reenviar]) para o
/// Agente conferir a correção antes de devolvê-la.
class CorrigirOcorrencia {
  CorrigirOcorrencia(this._repositorio, this._relogio);

  final RepositorioOcorrencias _repositorio;
  final Relogio _relogio;

  Future<ResultadoCorrecao> executar(
    OcorrenciaDetalhe atual,
    DadosOcorrencia dados,
    List<ArquivoEvidencia> novasEvidencias,
  ) async {
    final erros = dados.validar(_relogio.agora());
    if (erros.isNotEmpty) throw DadosOcorrenciaInvalidos(erros);
    final erroEvidencia = validarLoteEvidencias(
      novasEvidencias,
      jaAnexadas: atual.evidencias.length,
    );
    if (erroEvidencia != null) throw EvidenciaInvalida(erroEvidencia);

    final corrigida = await _repositorio.corrigir(atual.id, dados);
    final falhas = await enviarEvidenciasEmSequencia(_repositorio, atual.id, novasEvidencias);
    if (novasEvidencias.length == falhas.length) {
      return ResultadoCorrecao(corrigida, falhas);
    }
    return ResultadoCorrecao(await _repositorio.obter(atual.id), falhas);
  }
}
