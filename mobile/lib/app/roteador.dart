import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:material_ui/material_ui.dart';

import '../core/apresentacao/rotas.dart';
import '../features/autenticacao/application/controlador_sessao.dart';
import '../features/autenticacao/presentation/tela_login.dart';
import '../features/autenticacao/presentation/tela_sem_acesso.dart';
import '../features/notificacoes/presentation/tela_notificacoes.dart';
import '../features/ocorrencias/presentation/tela_corrigir_ocorrencia.dart';
import '../features/ocorrencias/presentation/tela_detalhe_ocorrencia.dart';
import '../features/ocorrencias/presentation/tela_minhas_ocorrencias.dart';
import '../features/ocorrencias/presentation/tela_registrar_ocorrencia.dart';
import '../features/preferencias/presentation/tela_ajustes.dart';
import '../features/revisao/presentation/tela_fila_revisao.dart';
import '../features/revisao/presentation/tela_revisar_ocorrencia.dart';
import 'casca.dart';
import 'guarda_rotas.dart';

final roteadorProvider = Provider<GoRouter>((ref) {
  final mudancaDeSessao = ValueNotifier<int>(0);
  ref.listen(controladorSessaoProvider, (_, _) => mudancaDeSessao.value++);
  final raiz = GlobalKey<NavigatorState>(debugLabel: 'raiz');
  final roteador = GoRouter(
    navigatorKey: raiz,
    initialLocation: Rotas.abertura,
    refreshListenable: mudancaDeSessao,
    redirect: (_, estado) =>
        redirecionar(ref.read(controladorSessaoProvider), estado.matchedLocation),
    routes: _rotas(raiz),
  );
  ref.onDispose(() {
    roteador.dispose();
    mudancaDeSessao.dispose();
  });
  return roteador;
});

String _id(GoRouterState estado) => estado.pathParameters['id']!;

/// As abas ficam num `StatefulShellRoute` (cada uma guarda rolagem e filtros).
/// Telas de fluxo usam o navegador [raiz]: abrem por cima, sem a barra inferior,
/// e o "voltar" retorna à aba de origem.
List<RouteBase> _rotas(GlobalKey<NavigatorState> raiz) => [
  GoRoute(path: Rotas.abertura, builder: (_, _) => const _TelaAbertura()),
  GoRoute(path: Rotas.login, builder: (_, _) => const TelaLogin()),
  GoRoute(path: Rotas.semAcesso, builder: (_, _) => const TelaSemAcesso()),
  StatefulShellRoute.indexedStack(
    builder: (_, _, navegacao) => CascaNavegacao(navegacao),
    branches: [
      for (final aba in Aba.values) StatefulShellBranch(routes: [_rotaDaAba(aba, raiz)]),
    ],
  ),
];

GoRoute _rotaDaAba(Aba aba, GlobalKey<NavigatorState> raiz) => switch (aba) {
  Aba.ocorrencias => GoRoute(
    path: Rotas.minhasOcorrencias,
    builder: (_, _) => const TelaMinhasOcorrencias(),
    routes: [
      GoRoute(
        path: 'nova',
        parentNavigatorKey: raiz,
        builder: (_, _) => const TelaRegistrarOcorrencia(),
      ),
      GoRoute(
        path: ':id',
        parentNavigatorKey: raiz,
        builder: (_, estado) => TelaDetalheOcorrencia(ocorrenciaId: _id(estado)),
        routes: [
          GoRoute(
            path: 'corrigir',
            parentNavigatorKey: raiz,
            builder: (_, estado) => TelaCorrigirOcorrencia(ocorrenciaId: _id(estado)),
          ),
        ],
      ),
    ],
  ),
  Aba.revisao => GoRoute(
    path: Rotas.filaRevisao,
    builder: (_, _) => const TelaFilaRevisao(),
    routes: [
      GoRoute(
        path: ':id',
        parentNavigatorKey: raiz,
        builder: (_, estado) => TelaRevisarOcorrencia(ocorrenciaId: _id(estado)),
      ),
    ],
  ),
  Aba.notificacoes => GoRoute(
    path: Rotas.notificacoes,
    builder: (_, _) => const TelaNotificacoes(),
  ),
  Aba.ajustes => GoRoute(path: Rotas.ajustes, builder: (_, _) => const TelaAjustes()),
};

/// Exibida só enquanto a sessão salva é restaurada na abertura do app.
class _TelaAbertura extends StatelessWidget {
  const _TelaAbertura();

  @override
  Widget build(BuildContext context) =>
      const Scaffold(body: Center(child: CircularProgressIndicator()));
}
