import 'arquivo_evidencia.dart';
import 'enums.dart';

final class Coordenada {
  const Coordenada({required this.latitude, required this.longitude});

  final double latitude;
  final double longitude;

  bool get valida => latitude >= -90 && latitude <= 90 && longitude >= -180 && longitude <= 180;
}

/// Pessoa qualificada na ocorrência. [id] só existe depois de persistida.
final class Envolvido {
  const Envolvido({
    required this.nome,
    required this.tipo,
    this.id,
    this.documento,
    this.email,
    this.telefone,
  });

  final String? id;
  final String nome;
  final TipoEnvolvido tipo;
  final String? documento;
  final String? email;
  final String? telefone;
}

final class Tipificacao {
  const Tipificacao({required this.artigo, required this.descricao});

  final String artigo;
  final String descricao;
}

/// Arquivo já vinculado à ocorrência, com hash SHA-256 calculado pelo backend.
final class Evidencia {
  const Evidencia({
    required this.id,
    required this.nomeOriginal,
    required this.formato,
    required this.tamanhoBytes,
    required this.hashSha256,
    required this.enviadaEm,
  });

  final String id;
  final String nomeOriginal;
  final String formato;
  final int tamanhoBytes;
  final String hashSha256;
  final DateTime enviadaEm;

  /// Fotos são exibidas no próprio app; PDFs ficam para o sistema web.
  bool get ehImagem => FormatoEvidencia.doCodigo(formato)?.ehImagem ?? false;
}

/// Entrada do histórico append-only de status (`historico_status_ocorrencia`).
final class RegistroHistoricoStatus {
  const RegistroHistoricoStatus({
    required this.para,
    required this.em,
    required this.porId,
    this.de,
    this.justificativa,
  });

  final StatusOcorrencia? de;
  final StatusOcorrencia para;
  final DateTime em;
  final String porId;
  final String? justificativa;
}

class OcorrenciaResumo {
  const OcorrenciaResumo({
    required this.id,
    required this.numeroProtocolo,
    required this.natureza,
    required this.localizacao,
    required this.coordenada,
    required this.status,
    required this.prioridade,
    required this.dataHoraFato,
    required this.criadaEm,
    required this.atualizadaEm,
    required this.agentePolicialId,
    required this.versao,
  });

  final String id;
  final String numeroProtocolo;
  final String natureza;
  final String localizacao;
  final Coordenada coordenada;
  final StatusOcorrencia status;
  final PrioridadeOcorrencia prioridade;
  final DateTime dataHoraFato;
  final DateTime criadaEm;
  final DateTime atualizadaEm;
  final String agentePolicialId;
  final int versao;
}

final class OcorrenciaDetalhe extends OcorrenciaResumo {
  const OcorrenciaDetalhe({
    required super.id,
    required super.numeroProtocolo,
    required super.natureza,
    required super.localizacao,
    required super.coordenada,
    required super.status,
    required super.prioridade,
    required super.dataHoraFato,
    required super.criadaEm,
    required super.atualizadaEm,
    required super.agentePolicialId,
    required super.versao,
    required this.descricao,
    required this.envolvidos,
    required this.tipificacoes,
    required this.evidencias,
    required this.historico,
    this.justificativaRevisao,
    this.hashNarrativa,
  });

  final String descricao;
  final List<Envolvido> envolvidos;
  final List<Tipificacao> tipificacoes;
  final List<Evidencia> evidencias;
  final List<RegistroHistoricoStatus> historico;

  /// Motivo da última devolução/rejeição escrito pelo Delegado.
  final String? justificativaRevisao;

  /// SHA-256 da narrativa, gravado quando o Delegado valida (RNF03).
  final String? hashNarrativa;
}

/// Comprovante devolvido ao registrar (UC01): protocolo para o cidadão e o Agente.
final class ProtocoloRegistrado {
  const ProtocoloRegistrado({
    required this.ocorrenciaId,
    required this.numeroProtocolo,
    required this.status,
    required this.criadaEm,
  });

  final String ocorrenciaId;
  final String numeroProtocolo;
  final StatusOcorrencia status;
  final DateTime criadaEm;
}

/// Critérios de `GET /v1/ocorrencias` usados pelo app (o Agente só recebe as próprias).
final class FiltroOcorrencias {
  const FiltroOcorrencias({
    this.status = const {},
    this.somenteMinhas = false,
    this.maisRecentesPrimeiro = false,
    this.ordenarPorPrioridade = false,
  });

  final Set<StatusOcorrencia> status;
  final bool somenteMinhas;
  final bool maisRecentesPrimeiro;
  final bool ordenarPorPrioridade;

  /// Igualdade por valor: o filtro é a chave das listas em cache no app.
  @override
  bool operator ==(Object other) =>
      other is FiltroOcorrencias &&
      other.somenteMinhas == somenteMinhas &&
      other.maisRecentesPrimeiro == maisRecentesPrimeiro &&
      other.ordenarPorPrioridade == ordenarPorPrioridade &&
      other.status.length == status.length &&
      other.status.containsAll(status);

  @override
  int get hashCode => Object.hash(
    somenteMinhas,
    maisRecentesPrimeiro,
    ordenarPorPrioridade,
    Object.hashAllUnordered(status),
  );
}
