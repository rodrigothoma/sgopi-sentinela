import 'package:go_router/go_router.dart';
import 'package:material_ui/material_ui.dart';

import '../../../core/apresentacao/contexto.dart';
import '../../../core/apresentacao/rotas.dart';
import '../../autenticacao/presentation/botao_sair.dart';
import '../domain/enums.dart';
import '../domain/ocorrencia.dart';
import 'rotulos.dart';
import 'widgets/lista_ocorrencias_paginada.dart';

/// Status que o Agente costuma acompanhar, na ordem do fluxo (UC01 → UC04).
const _filtrosAgente = [
  StatusOcorrencia.aguardandoRevisao,
  StatusOcorrencia.emCorrecao,
  StatusOcorrencia.validada,
  StatusOcorrencia.rejeitada,
];

/// Home do Agente: as próprias ocorrências, mais recentes primeiro.
class TelaMinhasOcorrencias extends StatefulWidget {
  const TelaMinhasOcorrencias({super.key});

  @override
  State<TelaMinhasOcorrencias> createState() => _TelaMinhasOcorrenciasState();
}

class _TelaMinhasOcorrenciasState extends State<TelaMinhasOcorrencias> {
  StatusOcorrencia? _status;

  FiltroOcorrencias get _filtro =>
      FiltroOcorrencias(status: {?_status}, somenteMinhas: true, maisRecentesPrimeiro: true);

  @override
  Widget build(BuildContext context) {
    final t = context.textos;
    return Scaffold(
      appBar: AppBar(
        title: Text(t.minhasTitulo),
        actions: const [BotaoSair()],
        bottom: PreferredSize(preferredSize: const Size.fromHeight(56), child: _chips(context)),
      ),
      body: ListaOcorrenciasPaginada(
        filtro: _filtro,
        mensagemVazia: t.listaVazia,
        aoTocar: (o) => context.push(Rotas.detalheOcorrencia(o.id)),
      ),
      floatingActionButton: FloatingActionButton.extended(
        key: const Key('minhas.registrar'),
        onPressed: () => context.push(Rotas.registrarOcorrencia),
        icon: const Icon(Icons.add),
        label: Text(t.registrarTitulo),
      ),
    );
  }

  Widget _chips(BuildContext context) => SizedBox(
    height: 56,
    child: ListView(
      scrollDirection: Axis.horizontal,
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      children: [
        for (final status in [null, ..._filtrosAgente])
          Padding(
            padding: const EdgeInsets.only(right: 8),
            child: ChoiceChip(
              label: Text(status?.rotulo(context.textos) ?? context.textos.filtroTodas),
              selected: _status == status,
              onSelected: (_) => setState(() => _status = status),
            ),
          ),
      ],
    ),
  );
}
