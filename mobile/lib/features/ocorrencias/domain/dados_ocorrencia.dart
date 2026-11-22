import 'enums.dart';
import 'ocorrencia.dart';

/// Regras de formulário iguais às de `backend/src/domain/ocorrencia/entity.py`.
/// Validar no app evita ida e volta à rede; o backend continua validando.
const tamanhoMinimoDescricao = 20;
const tamanhoDocumentoCpf = 11;
const tamanhoDocumentoRg = 10;

enum ErroOcorrencia {
  naturezaVazia,
  descricaoCurta,
  localizacaoVazia,
  coordenadaInvalida,
  dataFatoFutura,
  semEnvolvidos,
}

enum ErroEnvolvido { nomeVazio, nomeComNumeros, documentoInvalido }

final _digito = RegExp(r'\d');
final _separadoresDocumento = RegExp(r'[\s.\-/]');
final _somenteDigitos = RegExp(r'^\d+$');

/// Nome obrigatório e sem números (`envolvido.nome_invalido`).
ErroEnvolvido? validarNomeEnvolvido(String nome) {
  if (nome.trim().isEmpty) return ErroEnvolvido.nomeVazio;
  if (_digito.hasMatch(nome)) return ErroEnvolvido.nomeComNumeros;
  return null;
}

/// Documento opcional: só dígitos (máscara tolerada), 11 (CPF) ou 10 (RG).
ErroEnvolvido? validarDocumento(String? documento) {
  final valor = documento?.trim() ?? '';
  if (valor.isEmpty) return null;
  final digitos = valor.replaceAll(_separadoresDocumento, '');
  final tamanhoAceito =
      digitos.length == tamanhoDocumentoCpf || digitos.length == tamanhoDocumentoRg;
  if (!_somenteDigitos.hasMatch(digitos) || !tamanhoAceito) {
    return ErroEnvolvido.documentoInvalido;
  }
  return null;
}

Set<ErroEnvolvido> validarEnvolvido(Envolvido envolvido) => {
  ?validarNomeEnvolvido(envolvido.nome),
  ?validarDocumento(envolvido.documento),
};

/// Narrativa preenchida pelo Agente, usada tanto no registro quanto na correção.
final class DadosOcorrencia {
  const DadosOcorrencia({
    required this.natureza,
    required this.descricao,
    required this.localizacao,
    required this.coordenada,
    required this.dataHoraFato,
    required this.envolvidos,
    this.tipificacoes = const [],
    this.prioridade,
  });

  final String natureza;
  final String descricao;
  final String localizacao;
  final Coordenada? coordenada;
  final DateTime dataHoraFato;
  final List<Envolvido> envolvidos;
  final List<Tipificacao> tipificacoes;

  /// Opcional: ausente, o backend sugere pela natureza e tipificações.
  final PrioridadeOcorrencia? prioridade;

  Set<ErroOcorrencia> validar(DateTime agora) => {
    if (natureza.trim().isEmpty) ErroOcorrencia.naturezaVazia,
    if (descricao.trim().length < tamanhoMinimoDescricao) ErroOcorrencia.descricaoCurta,
    if (localizacao.trim().isEmpty) ErroOcorrencia.localizacaoVazia,
    if (!(coordenada?.valida ?? false)) ErroOcorrencia.coordenadaInvalida,
    if (dataHoraFato.isAfter(agora)) ErroOcorrencia.dataFatoFutura,
    if (envolvidos.isEmpty) ErroOcorrencia.semEnvolvidos,
  };
}

/// Narrativa recusada antes de ir ao backend; a tela destaca os campos em [erros].
final class DadosOcorrenciaInvalidos implements Exception {
  const DadosOcorrenciaInvalidos(this.erros);

  final Set<ErroOcorrencia> erros;
}
