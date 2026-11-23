import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:material_ui/material_ui.dart';

import '../core/apresentacao/contexto.dart';
import '../features/autenticacao/application/controlador_sessao.dart';
import '../features/notificacoes/application/notificacoes.dart';
import 'guarda_rotas.dart';

/// Barra inferior com as abas do papel e o selo de notificações não lidas.
class CascaNavegacao extends ConsumerWidget {
  const CascaNavegacao(this.navegacao, {super.key});

  final StatefulNavigationShell navegacao;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final papel = ref.watch(sessaoAtualProvider)?.usuario.papel;
    final abas = papel == null ? const <Aba>[] : abasDoPapel(papel);
    final atual = abas.indexWhere((aba) => aba.index == navegacao.currentIndex);
    if (abas.length < 2 || atual < 0) return navegacao;
    final naoLidas = ref.watch(naoLidasProvider).value ?? 0;
    return Scaffold(
      body: navegacao,
      bottomNavigationBar: NavigationBar(
        selectedIndex: atual,
        onDestinationSelected: (i) =>
            // Tocar na aba já aberta volta ao topo dela, como nos apps do sistema.
            navegacao.goBranch(abas[i].index, initialLocation: i == atual),
        destinations: [for (final aba in abas) _destino(context, aba, naoLidas)],
      ),
    );
  }

  NavigationDestination _destino(BuildContext context, Aba aba, int naoLidas) {
    final t = context.textos;
    final (rotulo, icone, iconeAtivo) = switch (aba) {
      Aba.ocorrencias => (t.abaOcorrencias, Icons.assignment_outlined, Icons.assignment),
      Aba.revisao => (t.abaFila, Icons.fact_check_outlined, Icons.fact_check),
      Aba.notificacoes => (t.abaNotificacoes, Icons.notifications_outlined, Icons.notifications),
      Aba.ajustes => (t.abaAjustes, Icons.settings_outlined, Icons.settings),
    };
    Widget comSelo(IconData i) => aba == Aba.notificacoes && naoLidas > 0
        ? Badge.count(count: naoLidas, child: Icon(i))
        : Icon(i);
    return NavigationDestination(
      key: Key('aba.${aba.name}'),
      icon: comSelo(icone),
      selectedIcon: comSelo(iconeAtivo),
      label: rotulo,
      tooltip: aba == Aba.notificacoes && naoLidas > 0 ? t.naoLidas(naoLidas) : null,
    );
  }
}
