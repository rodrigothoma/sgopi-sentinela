import '../../../core/dominio/relogio.dart';
import '../domain/arquivo_evidencia.dart';
import '../domain/dados_ocorrencia.dart';
import '../domain/ocorrencia.dart';
import '../domain/portas.dart';
import 'envio_evidencias.dart';

final class ResultadoRegistro {
  const ResultadoRegistro(this.protocolo, this.evidenciasNaoEnviadas);

  final ProtocoloRegistrado protocolo;
  final List<EnvioEvidenciaFalhou> evidenciasNaoEnviadas;
}

/// UC01 (RF01): o Agente registra a ocorrência e, em seguida, anexa as fotos.
class RegistrarOcorrencia {
  RegistrarOcorrencia(this._repositorio, this._relogio);

  final RepositorioOcorrencias _repositorio;
  final Relogio _relogio;

  /// Lança [DadosOcorrenciaInvalidos] ou [EvidenciaInvalida] antes de chamar o
  /// backend; falhas de rede ou de regra no backend chegam como `Falha`.
  Future<ResultadoRegistro> executar(
    DadosOcorrencia dados,
    List<ArquivoEvidencia> evidencias,
  ) async {
    final erros = dados.validar(_relogio.agora());
    if (erros.isNotEmpty) throw DadosOcorrenciaInvalidos(erros);
    final erroEvidencia = validarLoteEvidencias(evidencias);
    if (erroEvidencia != null) throw EvidenciaInvalida(erroEvidencia);

    final protocolo = await _repositorio.registrar(dados);
    final falhas = await enviarEvidenciasEmSequencia(
      _repositorio,
      protocolo.ocorrenciaId,
      evidencias,
    );
    return ResultadoRegistro(protocolo, falhas);
  }
}
