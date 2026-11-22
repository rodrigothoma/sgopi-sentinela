import 'package:material_ui/material_ui.dart';

/// Título de seção usado nos formulários e no detalhe da ocorrência.
class TituloSecao extends StatelessWidget {
  const TituloSecao(this.texto, {this.acao, super.key});

  final String texto;
  final Widget? acao;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(top: 20, bottom: 8),
    child: Row(
      children: [
        Expanded(child: Text(texto, style: Theme.of(context).textTheme.titleMedium)),
        ?acao,
      ],
    ),
  );
}
