import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:material_ui/material_ui.dart';

import '../../../core/apresentacao/contexto.dart';
import '../application/preferencias.dart';
import '../domain/preferencias.dart';
import 'rotulos.dart';

/// Atalhos de tema e idioma para telas sem a aba de Ajustes (login), como no web.
class BotoesPreferencias extends ConsumerWidget {
  const BotoesPreferencias({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = context.textos;
    final atual = ref.watch(controladorPreferenciasProvider);
    final controlador = ref.read(controladorPreferenciasProvider.notifier);
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        PopupMenuButton<IdiomaApp>(
          key: const Key('preferencias.idioma'),
          tooltip: t.alterarIdioma,
          icon: const Icon(Icons.translate),
          initialValue: atual.idioma,
          onSelected: controlador.definirIdioma,
          itemBuilder: (_) => [
            for (final i in IdiomaApp.values) PopupMenuItem(value: i, child: Text(i.rotulo(t))),
          ],
        ),
        PopupMenuButton<ModoTema>(
          key: const Key('preferencias.tema'),
          tooltip: t.alterarTema,
          icon: Icon(atual.tema.icone),
          initialValue: atual.tema,
          onSelected: controlador.definirTema,
          itemBuilder: (_) => [
            for (final m in ModoTema.values)
              PopupMenuItem(
                value: m,
                child: ListTile(
                  leading: Icon(m.icone),
                  title: Text(m.rotulo(t)),
                  contentPadding: EdgeInsets.zero,
                ),
              ),
          ],
        ),
      ],
    );
  }
}
