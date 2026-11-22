import 'papel.dart';

final class Usuario {
  const Usuario({required this.id, required this.nome, required this.login, required this.papel});

  final String id;
  final String nome;
  final String login;
  final Papel papel;
}
