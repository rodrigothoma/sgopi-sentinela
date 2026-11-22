import 'package:material_ui/material_ui.dart';

import '../design/tipografia.dart';

/// Círculo com as iniciais do nome, como o avatar da barra lateral do web.
class AvatarIniciais extends StatelessWidget {
  const AvatarIniciais(this.nome, {this.raio = 24, super.key});

  final String nome;
  final double raio;

  static String iniciaisDe(String nome) {
    final partes = nome.trim().split(RegExp(r'\s+')).where((p) => p.isNotEmpty).toList();
    if (partes.isEmpty) return '?';
    final primeira = partes.first[0];
    final ultima = partes.length > 1 ? partes.last[0] : '';
    return '$primeira$ultima'.toUpperCase();
  }

  @override
  Widget build(BuildContext context) {
    final cores = Theme.of(context).colorScheme;
    return CircleAvatar(
      radius: raio,
      backgroundColor: cores.primary,
      foregroundColor: cores.onPrimary,
      child: Text(
        iniciaisDe(nome),
        style: TextStyle(
          fontFamily: Fontes.destaque,
          fontWeight: FontWeight.w700,
          fontSize: raio * 0.8,
        ),
      ),
    );
  }
}
