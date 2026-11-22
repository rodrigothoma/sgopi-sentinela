import 'package:material_ui/material_ui.dart';

import '../../../../core/apresentacao/contexto.dart';
import '../../domain/dados_ocorrencia.dart';
import '../../domain/enums.dart';
import '../../domain/ocorrencia.dart';
import '../rotulos.dart';

/// Abre o cadastro de um envolvido; devolve `null` se o usuário cancelar.
Future<Envolvido?> abrirDialogoEnvolvido(BuildContext context, {Envolvido? inicial}) =>
    showDialog<Envolvido>(context: context, builder: (_) => _DialogoEnvolvido(inicial));

class _DialogoEnvolvido extends StatefulWidget {
  const _DialogoEnvolvido(this.inicial);

  final Envolvido? inicial;

  @override
  State<_DialogoEnvolvido> createState() => _DialogoEnvolvidoState();
}

class _DialogoEnvolvidoState extends State<_DialogoEnvolvido> {
  final _formulario = GlobalKey<FormState>();
  late final _nome = TextEditingController(text: widget.inicial?.nome);
  late final _documento = TextEditingController(text: widget.inicial?.documento);
  late final _email = TextEditingController(text: widget.inicial?.email);
  late final _telefone = TextEditingController(text: widget.inicial?.telefone);
  late TipoEnvolvido _tipo = widget.inicial?.tipo ?? TipoEnvolvido.vitima;

  @override
  void dispose() {
    for (final c in [_nome, _documento, _email, _telefone]) {
      c.dispose();
    }
    super.dispose();
  }

  void _confirmar() {
    if (!_formulario.currentState!.validate()) return;
    Navigator.of(context).pop(
      Envolvido(
        id: widget.inicial?.id,
        nome: _nome.text.trim(),
        tipo: _tipo,
        documento: _documento.text.trim(),
        email: _email.text.trim(),
        telefone: _telefone.text.trim(),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final t = context.textos;
    String? erro(ErroEnvolvido? e) => e == null ? null : mensagemErroEnvolvido(t, e);
    return AlertDialog(
      title: Text(t.envolvidoTitulo),
      content: Form(
        key: _formulario,
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextFormField(
                key: const Key('envolvido.nome'),
                controller: _nome,
                decoration: InputDecoration(labelText: t.campoNome),
                textCapitalization: TextCapitalization.words,
                validator: (v) => erro(validarNomeEnvolvido(v ?? '')),
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<TipoEnvolvido>(
                initialValue: _tipo,
                isExpanded: true,
                decoration: InputDecoration(labelText: t.campoTipo),
                items: [
                  for (final tipo in TipoEnvolvido.values)
                    DropdownMenuItem(value: tipo, child: Text(tipo.rotulo(t))),
                ],
                onChanged: (tipo) => setState(() => _tipo = tipo ?? _tipo),
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _documento,
                decoration: InputDecoration(labelText: t.campoDocumento),
                keyboardType: TextInputType.number,
                validator: (v) => erro(validarDocumento(v)),
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _email,
                decoration: InputDecoration(labelText: t.campoEmail),
                keyboardType: TextInputType.emailAddress,
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _telefone,
                decoration: InputDecoration(labelText: t.campoTelefone),
                keyboardType: TextInputType.phone,
              ),
            ],
          ),
        ),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.of(context).pop(), child: Text(t.cancelar)),
        FilledButton(
          key: const Key('envolvido.confirmar'),
          onPressed: _confirmar,
          child: Text(t.confirmar),
        ),
      ],
    );
  }
}
