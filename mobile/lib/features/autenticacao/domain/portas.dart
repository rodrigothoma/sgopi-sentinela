import 'sessao.dart';

/// Porta de saída para autenticar credenciais no backend (`POST /v1/auth/login`).
abstract interface class RepositorioAutenticacao {
  /// Lança `Falha` com `TipoFalha.naoAutenticado` (credenciais inválidas) ou
  /// `TipoFalha.muitasTentativas` (bloqueio por força bruta, com `aguardarPor`).
  Future<Sessao> entrar({required String login, required String senha});
}

/// Porta de saída para persistir a sessão entre aberturas do app, em local seguro.
abstract interface class ArmazenamentoSessao {
  Future<Sessao?> carregar();
  Future<void> salvar(Sessao sessao);
  Future<void> limpar();
}
