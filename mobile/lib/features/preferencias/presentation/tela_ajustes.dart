import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:material_ui/material_ui.dart';

import '../../../core/aplicacao/dependencias.dart';
import '../../../core/apresentacao/componentes/avatar_iniciais.dart';
import '../../../core/apresentacao/componentes/cartao_secao.dart';
import '../../../core/apresentacao/componentes/linha_info.dart';
import '../../../core/apresentacao/contexto.dart';
import '../../../core/apresentacao/design/tipografia.dart';
import '../../../core/config/ambiente.dart';
import '../../autenticacao/application/controlador_sessao.dart';
import '../../autenticacao/presentation/rotulos_papel.dart';
import '../application/preferencias.dart';
import '../domain/preferencias.dart';
import 'rotulos.dart';

/// Perfil, aparência, idioma, dados da sessão e saída.
class TelaAjustes extends ConsumerWidget {
  const TelaAjustes({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = context.textos;
    final sessao = ref.watch(sessaoAtualProvider);
    final preferencias = ref.watch(controladorPreferenciasProvider);
    final controlador = ref.read(controladorPreferenciasProvider.notifier);
    final tema = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: Text(t.abaAjustes)),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 32),
        children: [
          if (sessao != null)
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  children: [
                    AvatarIniciais(sessao.usuario.nome, raio: 28),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(sessao.usuario.nome, style: tema.textTheme.titleLarge),
                          Text(
                            '${sessao.usuario.papel.rotulo(t)} · ${sessao.usuario.login}',
                            style: tema.textTheme.bodyMedium?.copyWith(
                              color: tema.colorScheme.onSurfaceVariant,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
          const SizedBox(height: 16),
          CartaoSecao(
            titulo: t.secaoAparencia,
            icone: Icons.palette_outlined,
            filhos: [
              SegmentedButton<ModoTema>(
                key: const Key('ajustes.tema'),
                showSelectedIcon: false,
                segments: [
                  for (final m in ModoTema.values)
                    ButtonSegment(value: m, icon: Icon(m.icone), label: Text(m.rotulo(t))),
                ],
                selected: {preferencias.tema},
                onSelectionChanged: (s) => controlador.definirTema(s.single),
              ),
            ],
          ),
          const SizedBox(height: 16),
          CartaoSecao(
            titulo: t.secaoIdioma,
            icone: Icons.translate,
            filhos: [
              RadioGroup<IdiomaApp>(
                groupValue: preferencias.idioma,
                onChanged: (i) => controlador.definirIdioma(i!),
                child: Column(
                  children: [
                    for (final i in IdiomaApp.values)
                      RadioListTile<IdiomaApp>(
                        key: Key('ajustes.idioma.${i.name}'),
                        value: i,
                        title: Text(i.rotulo(t)),
                        contentPadding: EdgeInsets.zero,
                      ),
                  ],
                ),
              ),
              Text(
                t.ajudaIdioma,
                style: tema.textTheme.bodySmall?.copyWith(color: tema.colorScheme.onSurfaceVariant),
              ),
            ],
          ),
          const SizedBox(height: 16),
          CartaoSecao(
            titulo: t.secaoSobre,
            icone: Icons.info_outline,
            filhos: [
              if (sessao != null)
                LinhaInfo(
                  icone: Icons.schedule,
                  rotulo: t.rotuloSessao,
                  valor: t.sessaoExpiraAs(context.hora(sessao.expiraEm)),
                ),
              LinhaInfo(
                icone: Icons.dns_outlined,
                rotulo: t.rotuloServidor,
                valor: Ambiente.urlBaseApi,
                estiloValor: estiloMono(context),
              ),
              LinhaInfo(
                icone: Icons.tag,
                rotulo: t.rotuloVersao,
                valor: ref.watch(versaoAppProvider),
              ),
              ListTile(
                contentPadding: EdgeInsets.zero,
                leading: const Icon(Icons.description_outlined),
                title: Text(t.licencas),
                trailing: const Icon(Icons.chevron_right),
                onTap: () => showLicensePage(
                  context: context,
                  applicationName: t.appTitulo,
                  applicationVersion: ref.read(versaoAppProvider),
                ),
              ),
            ],
          ),
          const SizedBox(height: 24),
          OutlinedButton.icon(
            key: const Key('ajustes.sair'),
            style: OutlinedButton.styleFrom(
              foregroundColor: context.cores.perigo,
              side: BorderSide(color: context.cores.perigo.withValues(alpha: 0.5)),
            ),
            onPressed: () => _sair(context, ref),
            icon: const Icon(Icons.logout),
            label: Text(t.sair),
          ),
        ],
      ),
    );
  }

  Future<void> _sair(BuildContext context, WidgetRef ref) async {
    final t = context.textos;
    final confirmado = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(t.sair),
        content: Text(t.sairConfirmacao),
        actions: [
          TextButton(onPressed: () => Navigator.of(context).pop(false), child: Text(t.cancelar)),
          FilledButton(
            key: const Key('ajustes.confirmarSair'),
            style: FilledButton.styleFrom(backgroundColor: context.cores.perigo),
            onPressed: () => Navigator.of(context).pop(true),
            child: Text(t.sair),
          ),
        ],
      ),
    );
    if (confirmado ?? false) await ref.read(controladorSessaoProvider.notifier).sair();
  }
}
