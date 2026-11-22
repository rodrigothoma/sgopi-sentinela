import 'package:material_ui/material_ui.dart';

import '../../../core/apresentacao/contexto.dart';
import '../domain/decisao_revisao.dart';

enum TipoDecisao { validar, devolver, rejeitar }

/// Coleta o texto da decisão e devolve a [DecisaoRevisao] montada, ou `null` se cancelada.
/// Devolver e rejeitar exigem justificativa (validada pelo domínio).
Future<DecisaoRevisao?> abrirDialogoDecisao(BuildContext context, TipoDecisao tipo) =>
    showDialog<DecisaoRevisao>(context: context, builder: (_) => _DialogoDecisao(tipo));

class _DialogoDecisao extends StatefulWidget {
  const _DialogoDecisao(this.tipo);

  final TipoDecisao tipo;

  @override
  State<_DialogoDecisao> createState() => _DialogoDecisaoState();
}

class _DialogoDecisaoState extends State<_DialogoDecisao> {
  final _texto = TextEditingController();
  String? _erro;

  @override
  void dispose() {
    _texto.dispose();
    super.dispose();
  }

  DecisaoRevisao _montar() => switch (widget.tipo) {
    TipoDecisao.validar => Validar(despacho: _texto.text),
    TipoDecisao.devolver => Devolver(_texto.text),
    TipoDecisao.rejeitar => Rejeitar(_texto.text),
  };

  void _confirmar() {
    final decisao = _montar();
    if (decisao.validar().contains(ErroDecisao.justificativaCurta)) {
      setState(() => _erro = context.textos.erroJustificativaCurta(tamanhoMinimoJustificativa));
      return;
    }
    Navigator.of(context).pop(decisao);
  }

  @override
  Widget build(BuildContext context) {
    final t = context.textos;
    final (titulo, campo) = switch (widget.tipo) {
      TipoDecisao.validar => (t.validarTitulo, t.campoDespacho),
      TipoDecisao.devolver => (t.devolverTitulo, t.campoJustificativa),
      TipoDecisao.rejeitar => (t.rejeitarTitulo, t.campoJustificativa),
    };
    return AlertDialog(
      title: Text(titulo),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (widget.tipo == TipoDecisao.rejeitar) ...[
            Text(t.rejeitarAviso),
            const SizedBox(height: 12),
          ],
          TextField(
            key: const Key('decisao.texto'),
            controller: _texto,
            minLines: 3,
            maxLines: 6,
            decoration: InputDecoration(labelText: campo, errorText: _erro),
          ),
        ],
      ),
      actions: [
        TextButton(onPressed: () => Navigator.of(context).pop(), child: Text(t.cancelar)),
        FilledButton(
          key: const Key('decisao.confirmar'),
          onPressed: _confirmar,
          child: Text(t.confirmar),
        ),
      ],
    );
  }
}
