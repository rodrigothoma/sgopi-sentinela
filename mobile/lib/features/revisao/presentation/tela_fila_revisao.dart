import 'package:go_router/go_router.dart';
import 'package:material_ui/material_ui.dart';

import '../../../core/apresentacao/contexto.dart';
import '../../../core/apresentacao/rotas.dart';
import '../../autenticacao/presentation/botao_sair.dart';
import '../../ocorrencias/presentation/widgets/lista_ocorrencias_paginada.dart';
import '../application/fila_revisao.dart';

/// Home do Delegado: ocorrências aguardando revisão, as mais graves primeiro.
class TelaFilaRevisao extends StatelessWidget {
  const TelaFilaRevisao({super.key});

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: Text(context.textos.filaTitulo), actions: const [BotaoSair()]),
    body: ListaOcorrenciasPaginada(
      filtro: filtroFilaRevisao,
      mensagemVazia: context.textos.filaVazia,
      aoTocar: (o) => context.push(Rotas.revisarOcorrencia(o.id)),
    ),
  );
}
