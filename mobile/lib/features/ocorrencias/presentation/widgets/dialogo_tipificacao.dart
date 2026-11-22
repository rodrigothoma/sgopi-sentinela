import 'package:material_ui/material_ui.dart';

import '../../../../core/apresentacao/contexto.dart';
import '../../domain/ocorrencia.dart';

/// Abre o cadastro de uma tipificação penal; devolve `null` se o usuário cancelar.
Future<Tipificacao?> abrirDialogoTipificacao(BuildContext context) =>
    showDialog<Tipificacao>(context: context, builder: (_) => const _DialogoTipificacao());

class _DialogoTipificacao extends StatefulWidget {
  const _DialogoTipificacao();

  @override
  State<_DialogoTipificacao> createState() => _DialogoTipificacaoState();
}

class _DialogoTipificacaoState extends State<_DialogoTipificacao> {
  final _formulario = GlobalKey<FormState>();
  final _artigo = TextEditingController();
  final _descricao = TextEditingController();

  @override
  void dispose() {
    _artigo.dispose();
    _descricao.dispose();
    super.dispose();
  }

  void _confirmar() {
    if (!_formulario.currentState!.validate()) return;
    Navigator.of(context)
        .pop(Tipificacao(artigo: _artigo.text.trim(), descricao: _descricao.text.trim()));
  }

  @override
  Widget build(BuildContext context) {
    final t = context.textos;
    return AlertDialog(
      title: Text(t.tipificacaoTitulo),
      content: Form(
        key: _formulario,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextFormField(
              controller: _artigo,
              decoration: InputDecoration(labelText: t.campoArtigo, hintText: t.dicaArtigo),
              validator: (v) => (v ?? '').trim().isEmpty ? t.erroArtigoVazio : null,
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: _descricao,
              decoration: InputDecoration(labelText: t.campoDescricaoTipificacao),
              validator: (v) => (v ?? '').trim().isEmpty ? t.erroDescricaoTipificacaoVazia : null,
            ),
          ],
        ),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.of(context).pop(), child: Text(t.cancelar)),
        FilledButton(onPressed: _confirmar, child: Text(t.confirmar)),
      ],
    );
  }
}
