/// Limites de `backend/src/domain/ocorrencia/entity.py` e de `settings.py`.
const maximoEvidenciasPorOcorrencia = 10;
const tamanhoMaximoEvidenciaBytes = 10 * 1024 * 1024;

/// Formatos aceitos pelo backend; o formato é deduzido da extensão do nome.
enum FormatoEvidencia {
  jpeg('image/jpeg', {'jpg', 'jpeg'}),
  png('image/png', {'png'}),
  pdf('application/pdf', {'pdf'});

  const FormatoEvidencia(this.tipoMime, this.extensoes);

  final String tipoMime;
  final Set<String> extensoes;

  bool get ehImagem => this != pdf;

  static FormatoEvidencia? daExtensao(String nomeArquivo) {
    final ponto = nomeArquivo.lastIndexOf('.');
    return ponto < 0 ? null : doCodigo(nomeArquivo.substring(ponto + 1));
  }

  /// Formato como o backend informa em `EvidenciaSchema.formato` (`jpg`, `jpeg`, `png`, `pdf`).
  static FormatoEvidencia? doCodigo(String codigo) {
    final extensao = codigo.toLowerCase();
    for (final formato in values) {
      if (formato.extensoes.contains(extensao)) return formato;
    }
    return null;
  }
}

enum ErroEvidencia { formatoNaoSuportado, arquivoVazio, tamanhoExcedido, limiteAtingido }

/// Arquivo local escolhido pelo Agente, ainda não enviado.
final class ArquivoEvidencia {
  const ArquivoEvidencia({required this.caminho, required this.nome, required this.tamanhoBytes});

  final String caminho;
  final String nome;
  final int tamanhoBytes;

  FormatoEvidencia? get formato => FormatoEvidencia.daExtensao(nome);

  ErroEvidencia? validar() {
    if (formato == null) return ErroEvidencia.formatoNaoSuportado;
    if (tamanhoBytes <= 0) return ErroEvidencia.arquivoVazio;
    if (tamanhoBytes > tamanhoMaximoEvidenciaBytes) return ErroEvidencia.tamanhoExcedido;
    return null;
  }
}

/// Confere um lote de novos arquivos somando os já anexados ao limite por ocorrência.
ErroEvidencia? validarLoteEvidencias(List<ArquivoEvidencia> novos, {int jaAnexadas = 0}) {
  if (jaAnexadas + novos.length > maximoEvidenciasPorOcorrencia) {
    return ErroEvidencia.limiteAtingido;
  }
  for (final arquivo in novos) {
    final erro = arquivo.validar();
    if (erro != null) return erro;
  }
  return null;
}

final class EvidenciaInvalida implements Exception {
  const EvidenciaInvalida(this.erro);

  final ErroEvidencia erro;
}
