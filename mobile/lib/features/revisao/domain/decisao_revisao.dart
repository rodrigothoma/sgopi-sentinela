/// `TAMANHO_MINIMO_JUSTIFICATIVA` de `backend/src/domain/ocorrencia/entity.py`.
const tamanhoMinimoJustificativa = 10;

enum ErroDecisao { justificativaCurta }

/// Decisão do Delegado sobre uma ocorrência `AGUARDANDO_REVISAO` (UC04).
sealed class DecisaoRevisao {
  const DecisaoRevisao();

  Set<ErroDecisao> validar();
}

/// Valida a ocorrência; o backend calcula o hash SHA-256 da narrativa.
final class Validar extends DecisaoRevisao {
  const Validar({this.despacho});

  /// Observação opcional do Delegado registrada junto da validação.
  final String? despacho;

  @override
  Set<ErroDecisao> validar() => const {};
}

/// Decisões que exigem justificativa: o Agente autor é notificado com o motivo.
sealed class DecisaoJustificada extends DecisaoRevisao {
  const DecisaoJustificada(this.justificativa);

  final String justificativa;

  @override
  Set<ErroDecisao> validar() => {
    if (justificativa.trim().length < tamanhoMinimoJustificativa) ErroDecisao.justificativaCurta,
  };
}

/// Devolve ao Agente para correção (`EM_CORRECAO`).
final class Devolver extends DecisaoJustificada {
  const Devolver(super.justificativa);
}

/// Rejeita em definitivo (`REJEITADA`, estado final).
final class Rejeitar extends DecisaoJustificada {
  const Rejeitar(super.justificativa);
}

final class DecisaoInvalida implements Exception {
  const DecisaoInvalida(this.erros);

  final Set<ErroDecisao> erros;
}
