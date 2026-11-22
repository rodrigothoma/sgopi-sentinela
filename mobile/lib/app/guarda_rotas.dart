import 'package:riverpod/riverpod.dart';

import '../core/apresentacao/rotas.dart';
import '../features/autenticacao/application/controlador_sessao.dart';
import '../features/autenticacao/domain/papel.dart';
import '../features/autenticacao/domain/permissao.dart';

/// Tela inicial de cada papel: o app atende Agente (RF01) e Delegado (RF04).
String inicioDoPapel(Papel papel) {
  if (papel.pode(Permissao.registrarOcorrencia)) return Rotas.minhasOcorrencias;
  if (papel.pode(Permissao.revisarOcorrencia)) return Rotas.filaRevisao;
  return Rotas.semAcesso;
}

/// Decide para onde ir a cada navegação ou mudança de sessão (`null` = seguir).
///
/// Esconder telas não é segurança: o backend recusa com 403 o que o papel não pode.
/// A guarda só evita que o usuário caia num fluxo que não é o dele.
String? redirecionar(AsyncValue<EstadoSessao> estado, String destino) {
  final sessao = estado.value;
  if (sessao == null) return destino == Rotas.abertura ? null : Rotas.abertura;
  return switch (sessao) {
    SemSessao() => destino == Rotas.login ? null : Rotas.login,
    ComSessao(:final sessao) => _destinoPermitido(inicioDoPapel(sessao.usuario.papel), destino),
  };
}

String? _destinoPermitido(String inicio, String destino) {
  final dentroDoFluxo = destino == inicio || destino.startsWith('$inicio/');
  return dentroDoFluxo ? null : inicio;
}
