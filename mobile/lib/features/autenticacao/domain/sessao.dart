import 'usuario.dart';

/// Sessão de turno autenticada por JWT.
///
/// O backend emite tokens de 8 horas **sem refresh** (`jwt_expires_in_hours`):
/// expirado o prazo, o usuário precisa entrar de novo.
final class Sessao {
  const Sessao({required this.token, required this.expiraEm, required this.usuario});

  final String token;
  final DateTime expiraEm;
  final Usuario usuario;

  bool expiradaEm(DateTime instante) => !instante.isBefore(expiraEm);
}
