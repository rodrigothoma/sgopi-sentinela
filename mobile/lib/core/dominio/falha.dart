/// Categoria de uma falha vinda da borda (HTTP, plugins), independente da tecnologia.
///
/// Espelha o mapeamento de status do backend (`adapters/inbound/http/erros.py`):
/// 401, 403, 404, 409, 422, 429 e 5xx, mais a ausência de resposta.
enum TipoFalha {
  semConexao,
  naoAutenticado,
  acessoNegado,
  naoEncontrado,
  conflito,
  validacao,
  muitasTentativas,
  servidor,
  desconhecida,
}

/// Erro de negócio ou de infraestrutura entregue às camadas internas do app.
///
/// [detalhe] é a mensagem já traduzida pelo backend (campo `detail`, conforme
/// `Accept-Language`); [codigo] é a chave i18n estável (campo `code`, ex.:
/// `auth.credenciais_invalidas`) e [requestId] permite rastrear a chamada nos logs.
final class Falha implements Exception {
  const Falha(this.tipo, {this.detalhe, this.codigo, this.requestId, this.extra = const {}});

  static const _tamanhoReferencia = 8;

  final TipoFalha tipo;
  final String? detalhe;
  final String? codigo;
  final String? requestId;
  final Map<String, Object?> extra;

  /// Prefixo curto do `request_id`, exibido ao usuário como "(ref. abcd1234)".
  String? get referencia {
    final id = requestId;
    if (id == null || id.isEmpty) return null;
    return id.length <= _tamanhoReferencia ? id : id.substring(0, _tamanhoReferencia);
  }

  /// Tempo de bloqueio informado pelo backend em respostas 429 (`extra.retry_after_segundos`).
  Duration? get aguardarPor {
    final segundos = extra['retry_after_segundos'];
    return segundos is num ? Duration(seconds: segundos.ceil()) : null;
  }

  @override
  String toString() => 'Falha($tipo, codigo: $codigo, detalhe: $detalhe)';
}
