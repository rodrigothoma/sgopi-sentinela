import '../../../core/dominio/enum_api.dart';

/// Ciclo de vida da ocorrência (`backend/src/domain/ocorrencia/status.py`).
enum StatusOcorrencia implements EnumApi {
  aguardandoRevisao('AGUARDANDO_REVISAO'),
  emCorrecao('EM_CORRECAO'),
  rejeitada('REJEITADA'),
  validada('VALIDADA'),
  emAtendimento('EM_ATENDIMENTO'),
  encerrada('ENCERRADA'),
  arquivada('ARQUIVADA'),
  excluida('EXCLUIDA');

  const StatusOcorrencia(this.codigo);

  @override
  final String codigo;

  static StatusOcorrencia deCodigo(String codigo) => enumDeCodigo(values, codigo);

  /// O Agente autor só edita a narrativa depois que o Delegado devolve (UC04).
  bool get aceitaCorrecao => this == emCorrecao;

  /// Evidências só entram antes da decisão do Delegado (`exigir_anexo_permitido`).
  bool get aceitaEvidencia => this == aguardandoRevisao || this == emCorrecao;

  bool get aguardaRevisao => this == aguardandoRevisao;
}

/// Gravidade usada na triagem, da mais grave para a mais leve.
enum PrioridadeOcorrencia implements EnumApi {
  urgente('URGENTE'),
  alta('ALTA'),
  media('MEDIA'),
  baixa('BAIXA');

  const PrioridadeOcorrencia(this.codigo);

  @override
  final String codigo;

  static PrioridadeOcorrencia deCodigo(String codigo) => enumDeCodigo(values, codigo);
}

enum TipoEnvolvido implements EnumApi {
  vitima('VITIMA'),
  testemunha('TESTEMUNHA'),
  suspeito('SUSPEITO'),
  comunicante('COMUNICANTE');

  const TipoEnvolvido(this.codigo);

  @override
  final String codigo;

  static TipoEnvolvido deCodigo(String codigo) => enumDeCodigo(values, codigo);
}
