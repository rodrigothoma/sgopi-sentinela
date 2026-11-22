import 'package:riverpod/riverpod.dart';

import '../core/apresentacao/rotas.dart';
import '../features/autenticacao/application/controlador_sessao.dart';
import '../features/autenticacao/domain/papel.dart';
import '../features/autenticacao/domain/permissao.dart';

/// Abas da barra inferior, na ordem dos ramos do `StatefulShellRoute` em `roteador.dart`.
enum Aba {
  ocorrencias(Rotas.minhasOcorrencias),
  revisao(Rotas.filaRevisao),
  notificacoes(Rotas.notificacoes),
  ajustes(Rotas.ajustes);

  const Aba(this.caminho);

  final String caminho;
}

/// Abas visíveis para o papel: o fluxo principal (RF01 ou RF04) e as comuns.
/// Papéis sem fluxo no app não têm abas e veem a tela "use o sistema web".
List<Aba> abasDoPapel(Papel papel) {
  final principais = [
    if (papel.pode(Permissao.registrarOcorrencia)) Aba.ocorrencias,
    if (papel.pode(Permissao.revisarOcorrencia)) Aba.revisao,
  ];
  return principais.isEmpty ? const [] : [...principais, Aba.notificacoes, Aba.ajustes];
}

/// Tela inicial de cada papel: o app atende Agente (RF01) e Delegado (RF04).
String inicioDoPapel(Papel papel) => abasDoPapel(papel).firstOrNull?.caminho ?? Rotas.semAcesso;

/// Decide para onde ir a cada navegação ou mudança de sessão (`null` = seguir).
///
/// Esconder telas não é segurança: o backend recusa com 403 o que o papel não pode.
/// A guarda só evita que o usuário caia num fluxo que não é o dele.
String? redirecionar(AsyncValue<EstadoSessao> estado, String destino) {
  final sessao = estado.value;
  if (sessao == null) return destino == Rotas.abertura ? null : Rotas.abertura;
  return switch (sessao) {
    SemSessao() => destino == Rotas.login ? null : Rotas.login,
    ComSessao(:final sessao) => _destinoPermitido(sessao.usuario.papel, destino),
  };
}

String? _destinoPermitido(Papel papel, String destino) {
  bool dentroDe(String caminho) => destino == caminho || destino.startsWith('$caminho/');
  final abas = abasDoPapel(papel);
  if (abas.isEmpty) return destino == Rotas.semAcesso ? null : Rotas.semAcesso;
  return abas.any((aba) => dentroDe(aba.caminho)) ? null : abas.first.caminho;
}
