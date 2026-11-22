import 'dart:typed_data';

import '../../../core/dominio/pagina.dart';
import 'arquivo_evidencia.dart';
import 'dados_ocorrencia.dart';
import 'ocorrencia.dart';

/// Porta de saída para as ocorrências no backend (RF01). Erros chegam como `Falha`.
abstract interface class RepositorioOcorrencias {
  Future<Pagina<OcorrenciaResumo>> listar(
    FiltroOcorrencias filtro, {
    required int limite,
    required int deslocamento,
  });

  Future<OcorrenciaDetalhe> obter(String ocorrenciaId);

  /// Cria a ocorrência em `AGUARDANDO_REVISAO` (somente AGENTE).
  Future<ProtocoloRegistrado> registrar(DadosOcorrencia dados);

  /// Substitui a narrativa enquanto a ocorrência está `EM_CORRECAO` (somente o autor).
  Future<OcorrenciaDetalhe> corrigir(String ocorrenciaId, DadosOcorrencia dados);

  /// Devolve a ocorrência corrigida à fila do Delegado.
  Future<OcorrenciaDetalhe> reenviar(String ocorrenciaId);

  Future<Evidencia> anexarEvidencia(String ocorrenciaId, ArquivoEvidencia arquivo);

  /// Conteúdo da evidência para quem pode consultar a ocorrência. Falha `conflito`
  /// quando o hash do arquivo armazenado diverge do registrado (RF22).
  Future<Uint8List> baixarEvidencia(String ocorrenciaId, String evidenciaId);
}

enum MotivoLocalizacaoIndisponivel { servicoDesligado, permissaoNegada, falhaLeitura }

final class LocalizacaoIndisponivel implements Exception {
  const LocalizacaoIndisponivel(this.motivo);

  final MotivoLocalizacaoIndisponivel motivo;
}

/// Porta de saída para o GPS do aparelho, usada para georreferenciar o fato.
abstract interface class PortaLocalizacao {
  /// Lança [LocalizacaoIndisponivel] quando não há como obter a posição.
  Future<Coordenada> obterAtual();
}

enum OrigemImagem { camera, galeria }

/// Porta de saída para obter uma foto do aparelho como evidência.
abstract interface class PortaSeletorImagem {
  /// `null` quando o usuário cancela.
  Future<ArquivoEvidencia?> selecionar(OrigemImagem origem);
}
