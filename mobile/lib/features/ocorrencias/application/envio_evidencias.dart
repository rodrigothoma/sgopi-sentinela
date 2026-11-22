import '../domain/arquivo_evidencia.dart';
import '../domain/portas.dart';

/// Arquivo que não chegou ao backend, com o erro recebido (normalmente uma `Falha`).
final class EnvioEvidenciaFalhou {
  const EnvioEvidenciaFalhou(this.arquivo, this.erro);

  final ArquivoEvidencia arquivo;
  final Object erro;
}

/// Envia as evidências uma a uma, sem interromper o lote quando uma falha.
///
/// O registro da ocorrência já foi aceito quando isto roda, então uma foto
/// recusada não desfaz o protocolo: ela volta na lista para nova tentativa.
Future<List<EnvioEvidenciaFalhou>> enviarEvidenciasEmSequencia(
  RepositorioOcorrencias repositorio,
  String ocorrenciaId,
  List<ArquivoEvidencia> arquivos,
) async {
  final falhas = <EnvioEvidenciaFalhou>[];
  for (final arquivo in arquivos) {
    try {
      await repositorio.anexarEvidencia(ocorrenciaId, arquivo);
    } on Exception catch (erro) {
      falhas.add(EnvioEvidenciaFalhou(arquivo, erro));
    }
  }
  return falhas;
}
