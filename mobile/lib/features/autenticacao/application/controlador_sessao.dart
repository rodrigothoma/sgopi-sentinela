import 'package:riverpod/riverpod.dart';

import '../../../core/aplicacao/dependencias.dart';
import '../domain/sessao.dart';
import 'dependencias.dart';

sealed class EstadoSessao {
  const EstadoSessao();
}

final class SemSessao extends EstadoSessao {
  const SemSessao({this.expirou = false});

  /// Verdadeiro quando a saída foi forçada (token vencido ou 401), para avisar o usuário.
  final bool expirou;
}

final class ComSessao extends EstadoSessao {
  const ComSessao(this.sessao);

  final Sessao sessao;
}

final controladorSessaoProvider = AsyncNotifierProvider<ControladorSessao, EstadoSessao>(
  ControladorSessao.new,
);

/// Dono do ciclo de vida da sessão: restaura ao abrir o app, entra, sai e expira.
class ControladorSessao extends AsyncNotifier<EstadoSessao> {
  @override
  Future<EstadoSessao> build() async {
    final salva = await ref.read(armazenamentoSessaoProvider).carregar();
    if (salva == null) return const SemSessao();
    if (salva.expiradaEm(ref.read(relogioProvider).agora())) {
      await ref.read(armazenamentoSessaoProvider).limpar();
      return const SemSessao(expirou: true);
    }
    return ComSessao(salva);
  }

  /// Lança `Falha` sem alterar o estado, para a tela de login exibir o motivo.
  Future<void> entrar({required String login, required String senha}) async {
    final sessao = await ref
        .read(repositorioAutenticacaoProvider)
        .entrar(login: login.trim(), senha: senha);
    await ref.read(armazenamentoSessaoProvider).salvar(sessao);
    state = AsyncData(ComSessao(sessao));
  }

  Future<void> sair() => _encerrar(expirou: false);

  /// Chamado quando o backend responde 401 ou o prazo do token acaba.
  Future<void> expirar() async {
    if (state.value is ComSessao) await _encerrar(expirou: true);
  }

  /// Token utilizável agora; encerra a sessão se o prazo já passou.
  String? tokenVigente() {
    final atual = state.value;
    if (atual is! ComSessao) return null;
    if (atual.sessao.expiradaEm(ref.read(relogioProvider).agora())) {
      expirar();
      return null;
    }
    return atual.sessao.token;
  }

  Future<void> _encerrar({required bool expirou}) async {
    await ref.read(armazenamentoSessaoProvider).limpar();
    state = AsyncData(SemSessao(expirou: expirou));
  }
}

/// Atalho para a sessão ativa (ou `null`), usado por telas e guardas de rota.
final sessaoAtualProvider = Provider<Sessao?>((ref) {
  final estado = ref.watch(controladorSessaoProvider).value;
  return estado is ComSessao ? estado.sessao : null;
});
