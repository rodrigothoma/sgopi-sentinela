import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:material_ui/material_ui.dart';

import '../core/apresentacao/rotas.dart';
import '../features/autenticacao/application/controlador_sessao.dart';
import '../features/autenticacao/presentation/tela_login.dart';
import '../features/autenticacao/presentation/tela_sem_acesso.dart';
import '../features/ocorrencias/presentation/tela_corrigir_ocorrencia.dart';
import '../features/ocorrencias/presentation/tela_detalhe_ocorrencia.dart';
import '../features/ocorrencias/presentation/tela_minhas_ocorrencias.dart';
import '../features/ocorrencias/presentation/tela_registrar_ocorrencia.dart';
import '../features/revisao/presentation/tela_fila_revisao.dart';
import '../features/revisao/presentation/tela_revisar_ocorrencia.dart';
import 'guarda_rotas.dart';

final roteadorProvider = Provider<GoRouter>((ref) {
  final mudancaDeSessao = ValueNotifier<int>(0);
  ref.listen(controladorSessaoProvider, (_, _) => mudancaDeSessao.value++);
  final roteador = GoRouter(
    initialLocation: Rotas.abertura,
    refreshListenable: mudancaDeSessao,
    redirect: (_, estado) =>
        redirecionar(ref.read(controladorSessaoProvider), estado.matchedLocation),
    routes: _rotas,
  );
  ref.onDispose(() {
    roteador.dispose();
    mudancaDeSessao.dispose();
  });
  return roteador;
});

String _id(GoRouterState estado) => estado.pathParameters['id']!;

final _rotas = <RouteBase>[
  GoRoute(path: Rotas.abertura, builder: (_, _) => const _TelaAbertura()),
  GoRoute(path: Rotas.login, builder: (_, _) => const TelaLogin()),
  GoRoute(path: Rotas.semAcesso, builder: (_, _) => const TelaSemAcesso()),
  GoRoute(
    path: Rotas.minhasOcorrencias,
    builder: (_, _) => const TelaMinhasOcorrencias(),
    routes: [
      GoRoute(path: 'nova', builder: (_, _) => const TelaRegistrarOcorrencia()),
      GoRoute(
        path: ':id',
        builder: (_, estado) => TelaDetalheOcorrencia(ocorrenciaId: _id(estado)),
        routes: [
          GoRoute(
            path: 'corrigir',
            builder: (_, estado) => TelaCorrigirOcorrencia(ocorrenciaId: _id(estado)),
          ),
        ],
      ),
    ],
  ),
  GoRoute(
    path: Rotas.filaRevisao,
    builder: (_, _) => const TelaFilaRevisao(),
    routes: [
      GoRoute(
        path: ':id',
        builder: (_, estado) => TelaRevisarOcorrencia(ocorrenciaId: _id(estado)),
      ),
    ],
  ),
];

/// Exibida só enquanto a sessão salva é restaurada na abertura do app.
class _TelaAbertura extends StatelessWidget {
  const _TelaAbertura();

  @override
  Widget build(BuildContext context) =>
      const Scaffold(body: Center(child: CircularProgressIndicator()));
}
