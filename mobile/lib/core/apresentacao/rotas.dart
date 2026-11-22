/// Caminhos de navegação do app (go_router), num só lugar para telas e roteador.
abstract final class Rotas {
  static const abertura = '/';
  static const login = '/login';
  static const semAcesso = '/sem-acesso';
  static const minhasOcorrencias = '/ocorrencias';
  static const registrarOcorrencia = '/ocorrencias/nova';
  static const filaRevisao = '/revisao';

  static String detalheOcorrencia(String id) => '/ocorrencias/$id';
  static String corrigirOcorrencia(String id) => '/ocorrencias/$id/corrigir';
  static String revisarOcorrencia(String id) => '/revisao/$id';
}
