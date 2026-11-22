import 'package:flutter_svg/flutter_svg.dart';
import 'package:material_ui/material_ui.dart';

/// Distintivo do SGOPI (`assets/logo.svg`, derivado de `frontend/public/logo.svg`).
class LogoSgopi extends StatelessWidget {
  const LogoSgopi({this.tamanho = 72, this.cor, super.key});

  final double tamanho;
  final Color? cor;

  @override
  Widget build(BuildContext context) => SvgPicture.asset(
    'assets/logo.svg',
    width: tamanho,
    height: tamanho,
    semanticsLabel: 'SGOPI',
    colorFilter: ColorFilter.mode(cor ?? Theme.of(context).colorScheme.primary, BlendMode.srcIn),
  );
}
