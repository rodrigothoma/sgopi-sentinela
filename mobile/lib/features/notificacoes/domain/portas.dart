import 'notificacao.dart';

/// Porta de saída para as notificações do usuário logado. Erros chegam como `Falha`.
abstract interface class RepositorioNotificacoes {
  Future<LoteNotificacoes> listar({required int limite, required int deslocamento});

  Future<int> contarNaoLidas();

  Future<void> marcarLida(String notificacaoId);

  Future<void> marcarTodasLidas();
}
