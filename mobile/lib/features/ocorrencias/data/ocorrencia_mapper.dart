import '../../../core/dominio/pagina.dart';
import '../../../core/http/json.dart';
import '../domain/dados_ocorrencia.dart';
import '../domain/enums.dart';
import '../domain/ocorrencia.dart';

/// Tradução entre o JSON de `/v1/ocorrencias` e as entidades do app.
/// Espelha os schemas de `backend/src/adapters/inbound/http/v1/ocorrencias_router.py`.
abstract final class OcorrenciaMapper {
  static Pagina<OcorrenciaResumo> paginaDeJson(Json json) => Pagina(
    itens: lista(json, 'itens').map(resumoDeJson).toList(),
    total: campo<int>(json, 'total'),
    limite: campo<int>(json, 'limit'),
    deslocamento: campo<int>(json, 'offset'),
  );

  static OcorrenciaResumo resumoDeJson(Json json) => OcorrenciaResumo(
    id: campo<String>(json, 'ocorrencia_id'),
    numeroProtocolo: campo<String>(json, 'numero_protocolo'),
    natureza: campo<String>(json, 'natureza'),
    localizacao: campo<String>(json, 'localizacao'),
    coordenada: _coordenada(json),
    status: StatusOcorrencia.deCodigo(campo<String>(json, 'status')),
    prioridade: _prioridade(json),
    dataHoraFato: data(json, 'data_hora_fato'),
    criadaEm: data(json, 'criada_em'),
    atualizadaEm: data(json, 'atualizada_em'),
    agentePolicialId: campo<String>(json, 'agente_policial_id'),
    versao: campo<int>(json, 'versao'),
  );

  static OcorrenciaDetalhe detalheDeJson(Json json) {
    final resumo = resumoDeJson(json);
    return OcorrenciaDetalhe(
      id: resumo.id,
      numeroProtocolo: resumo.numeroProtocolo,
      natureza: resumo.natureza,
      localizacao: resumo.localizacao,
      coordenada: resumo.coordenada,
      status: resumo.status,
      prioridade: resumo.prioridade,
      dataHoraFato: resumo.dataHoraFato,
      criadaEm: resumo.criadaEm,
      atualizadaEm: resumo.atualizadaEm,
      agentePolicialId: resumo.agentePolicialId,
      versao: resumo.versao,
      descricao: campo<String>(json, 'descricao'),
      justificativaRevisao: campoOpcional<String>(json, 'justificativa_revisao'),
      hashNarrativa: campoOpcional<String>(json, 'hash_narrativa'),
      envolvidos: lista(json, 'envolvidos').map(_envolvido).toList(),
      tipificacoes: lista(json, 'tipificacoes').map(_tipificacao).toList(),
      evidencias: lista(json, 'evidencias').map(evidenciaDeJson).toList(),
      historico: lista(json, 'historico_status').map(_historico).toList(),
    );
  }

  static ProtocoloRegistrado protocoloDeJson(Json json) => ProtocoloRegistrado(
    ocorrenciaId: campo<String>(json, 'ocorrencia_id'),
    numeroProtocolo: campo<String>(json, 'numero_protocolo'),
    status: StatusOcorrencia.deCodigo(campo<String>(json, 'status')),
    criadaEm: data(json, 'criada_em'),
  );

  static Evidencia evidenciaDeJson(Json json) => Evidencia(
    id: campo<String>(json, 'id'),
    nomeOriginal: campo<String>(json, 'nome_original'),
    formato: campo<String>(json, 'formato'),
    tamanhoBytes: campo<int>(json, 'tamanho'),
    hashSha256: campo<String>(json, 'hash_sha256'),
    enviadaEm: data(json, 'enviada_em'),
  );

  /// Corpo de `POST /v1/ocorrencias`; `prioridade` só vai quando o Agente escolhe.
  static Json registroParaJson(DadosOcorrencia dados) => {
    ...correcaoParaJson(dados),
    if (dados.prioridade != null) 'prioridade': dados.prioridade!.codigo,
  };

  /// Corpo de `PUT /v1/ocorrencias/{id}`: a correção substitui a narrativa inteira.
  static Json correcaoParaJson(DadosOcorrencia dados) => {
    'natureza': dados.natureza.trim(),
    'descricao': dados.descricao.trim(),
    'localizacao': dados.localizacao.trim(),
    'latitude': dados.coordenada?.latitude,
    'longitude': dados.coordenada?.longitude,
    'data_hora_fato': dataParaApi(dados.dataHoraFato),
    'envolvidos': dados.envolvidos.map(_envolvidoParaJson).toList(),
    'tipificacoes': dados.tipificacoes
        .map((t) => {'artigo': t.artigo.trim(), 'descricao': t.descricao.trim()})
        .toList(),
  };

  static Coordenada _coordenada(Json json) =>
      Coordenada(latitude: numero(json, 'latitude'), longitude: numero(json, 'longitude'));

  static PrioridadeOcorrencia _prioridade(Json json) {
    final codigo = campoOpcional<String>(json, 'prioridade');
    return codigo == null ? PrioridadeOcorrencia.media : PrioridadeOcorrencia.deCodigo(codigo);
  }

  static Envolvido _envolvido(Json json) => Envolvido(
    id: campoOpcional<String>(json, 'id'),
    nome: campo<String>(json, 'nome'),
    tipo: TipoEnvolvido.deCodigo(campo<String>(json, 'tipo')),
    documento: campoOpcional<String>(json, 'documento'),
    email: campoOpcional<String>(json, 'email'),
    telefone: campoOpcional<String>(json, 'telefone'),
  );

  static Json _envolvidoParaJson(Envolvido e) => {
    'nome': e.nome.trim(),
    'tipo': e.tipo.codigo,
    'documento': _textoOuNulo(e.documento),
    'email': _textoOuNulo(e.email),
    'telefone': _textoOuNulo(e.telefone),
  };

  static Tipificacao _tipificacao(Json json) => Tipificacao(
    artigo: campo<String>(json, 'artigo'),
    descricao: campo<String>(json, 'descricao'),
  );

  static RegistroHistoricoStatus _historico(Json json) {
    final de = campoOpcional<String>(json, 'de');
    return RegistroHistoricoStatus(
      de: de == null ? null : StatusOcorrencia.deCodigo(de),
      para: StatusOcorrencia.deCodigo(campo<String>(json, 'para')),
      em: data(json, 'em'),
      porId: campo<String>(json, 'por_id'),
      justificativa: campoOpcional<String>(json, 'justificativa'),
    );
  }

  static String? _textoOuNulo(String? valor) {
    final texto = valor?.trim() ?? '';
    return texto.isEmpty ? null : texto;
  }
}
