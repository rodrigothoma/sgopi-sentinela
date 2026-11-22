import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:material_ui/material_ui.dart';

import '../../../../core/apresentacao/componentes/cartao_secao.dart';
import '../../../../core/apresentacao/componentes/linha_info.dart';
import '../../../../core/apresentacao/contexto.dart';
import '../../../../core/apresentacao/design/tipografia.dart';
import '../../application/conteudo_evidencia.dart';
import '../../domain/ocorrencia.dart';
import '../rotulos.dart';
import '../tela_evidencia.dart';
import 'selo_prioridade.dart';
import 'selo_status.dart';

const _espaco = SizedBox(height: 12);

/// Leitura completa da ocorrência, compartilhada pelo detalhe do Agente e pela revisão do Delegado.
class CorpoDetalheOcorrencia extends StatelessWidget {
  const CorpoDetalheOcorrencia(this.ocorrencia, {super.key});

  final OcorrenciaDetalhe ocorrencia;

  @override
  Widget build(BuildContext context) {
    final t = context.textos;
    final o = ocorrencia;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _cabecalho(context),
        if (o.justificativaRevisao != null) ...[
          _espaco,
          _justificativa(context, o.justificativaRevisao!),
        ],
        _espaco,
        CartaoSecao(
          titulo: t.secaoFato,
          icone: Icons.event_note_outlined,
          filhos: [
            LinhaInfo(
              icone: Icons.event,
              rotulo: t.rotuloFato,
              valor: context.dataHora(o.dataHoraFato),
            ),
            LinhaInfo(icone: Icons.place_outlined, rotulo: t.rotuloLocal, valor: o.localizacao),
            LinhaInfo(
              icone: Icons.my_location,
              rotulo: t.rotuloCoordenadas,
              valor:
                  '${o.coordenada.latitude.toStringAsFixed(6)}, '
                  '${o.coordenada.longitude.toStringAsFixed(6)}',
              estiloValor: estiloMono(context),
            ),
            LinhaInfo(
              icone: Icons.edit_calendar_outlined,
              rotulo: t.rotuloRegistradaEm,
              valor: context.dataHora(o.criadaEm),
            ),
          ],
        ),
        _espaco,
        CartaoSecao(
          titulo: t.rotuloDescricao,
          icone: Icons.notes,
          filhos: [SelectableText(o.descricao)],
        ),
        _espaco,
        CartaoSecao(
          titulo: t.secaoEnvolvidos,
          icone: Icons.people_outline,
          filhos: _ouNenhum(context, [
            for (final e in o.envolvidos)
              _linha(Icons.person_outline, e.nome, [e.tipo.rotulo(t), ?e.documento].join(' · ')),
          ]),
        ),
        _espaco,
        CartaoSecao(
          titulo: t.secaoTipificacoes,
          icone: Icons.gavel_outlined,
          filhos: _ouNenhum(context, [
            for (final tp in o.tipificacoes) _linha(Icons.gavel_outlined, tp.artigo, tp.descricao),
          ]),
        ),
        _espaco,
        CartaoSecao(
          titulo: t.secaoEvidencias,
          icone: Icons.photo_library_outlined,
          filhos: _ouNenhum(context, [
            for (final ev in o.evidencias) _LinhaEvidencia(ocorrenciaId: o.id, evidencia: ev),
          ]),
        ),
        _espaco,
        CartaoSecao(
          titulo: t.rotuloHistorico,
          icone: Icons.history,
          filhos: [
            for (final (i, h) in o.historico.reversed.indexed)
              _EtapaHistorico(registro: h, ultima: i == o.historico.length - 1),
          ],
        ),
        if (o.hashNarrativa != null) ...[
          _espaco,
          CartaoSecao(
            titulo: t.rotuloHashNarrativa,
            icone: Icons.verified_outlined,
            filhos: [
              SelectableText(
                o.hashNarrativa!,
                style: estiloMono(context, base: Theme.of(context).textTheme.bodySmall),
              ),
            ],
          ),
        ],
      ],
    );
  }

  Widget _cabecalho(BuildContext context) {
    final tema = Theme.of(context);
    final o = ocorrencia;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Wrap(
              alignment: WrapAlignment.spaceBetween,
              crossAxisAlignment: WrapCrossAlignment.center,
              spacing: 8,
              runSpacing: 4,
              children: [
                Text(
                  o.numeroProtocolo,
                  style: estiloMono(
                    context,
                    base: tema.textTheme.labelLarge,
                  ).copyWith(color: tema.colorScheme.onSurfaceVariant),
                ),
                SeloStatus(o.status),
              ],
            ),
            const SizedBox(height: 8),
            Text(o.natureza, style: tema.textTheme.headlineSmall),
            const SizedBox(height: 4),
            SeloPrioridade(o.prioridade),
          ],
        ),
      ),
    );
  }

  Widget _justificativa(BuildContext context, String texto) {
    final cor = context.cores.correcao;
    return DecoratedBox(
      decoration: BoxDecoration(
        color: cor.withValues(alpha: 0.10),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: cor.withValues(alpha: 0.4)),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(Icons.feedback_outlined, color: cor),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    context.textos.rotuloJustificativaDelegado,
                    style: Theme.of(context).textTheme.titleSmall?.copyWith(color: cor),
                  ),
                  const SizedBox(height: 4),
                  Text(texto),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _linha(IconData icone, String titulo, String subtitulo) => ListTile(
    dense: true,
    contentPadding: EdgeInsets.zero,
    leading: Icon(icone),
    title: Text(titulo),
    subtitle: subtitulo.isEmpty ? null : Text(subtitulo),
  );

  List<Widget> _ouNenhum(BuildContext context, List<Widget> itens) => itens.isEmpty
      ? [
          Text(
            context.textos.nenhumItem,
            style: TextStyle(color: Theme.of(context).colorScheme.onSurfaceVariant),
          ),
        ]
      : itens;
}

/// Fotos com miniatura (abrem em tela cheia); PDF ainda não tem visualizador no app.
class _LinhaEvidencia extends StatelessWidget {
  const _LinhaEvidencia({required this.ocorrenciaId, required this.evidencia});

  final String ocorrenciaId;
  final Evidencia evidencia;

  @override
  Widget build(BuildContext context) {
    final t = context.textos;
    final data = context.dataHora(evidencia.enviadaEm);
    if (!evidencia.ehImagem) {
      return ListTile(
        dense: true,
        contentPadding: EdgeInsets.zero,
        leading: const Icon(Icons.picture_as_pdf_outlined),
        title: Text(evidencia.nomeOriginal),
        subtitle: Text('$data\n${t.pdfSomenteWeb}'),
      );
    }
    return ListTile(
      key: Key('evidencia.${evidencia.id}'),
      contentPadding: EdgeInsets.zero,
      leading: _Miniatura(ocorrenciaId: ocorrenciaId, evidencia: evidencia),
      title: Text(evidencia.nomeOriginal, maxLines: 1, overflow: TextOverflow.ellipsis),
      subtitle: Text(data),
      trailing: Icon(Icons.zoom_in, semanticLabel: t.verEvidencia),
      onTap: () => abrirEvidencia(context, ocorrenciaId, evidencia),
    );
  }
}

/// Usa o mesmo download da tela cheia: abrir a foto depois não baixa de novo.
class _Miniatura extends ConsumerWidget {
  const _Miniatura({required this.ocorrenciaId, required this.evidencia});

  final String ocorrenciaId;
  final Evidencia evidencia;

  static const _lado = 48.0;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final bytes = ref
        .watch(conteudoEvidenciaProvider((ocorrenciaId: ocorrenciaId, evidenciaId: evidencia.id)))
        .value;
    final cor = Theme.of(context).colorScheme.surfaceContainerHighest;
    return ClipRRect(
      borderRadius: BorderRadius.circular(8),
      child: SizedBox.square(
        dimension: _lado,
        child: bytes == null
            ? ColoredBox(color: cor, child: const Icon(Icons.image_outlined))
            : Image.memory(
                bytes,
                fit: BoxFit.cover,
                cacheWidth: 144,
                errorBuilder: (_, _, _) =>
                    ColoredBox(color: cor, child: const Icon(Icons.broken_image_outlined)),
              ),
      ),
    );
  }
}

/// Etapa da linha do tempo de status (mais recente no topo).
class _EtapaHistorico extends StatelessWidget {
  const _EtapaHistorico({required this.registro, required this.ultima});

  final RegistroHistoricoStatus registro;
  final bool ultima;

  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);
    final cor = registro.para.cor(context.cores);
    return IntrinsicHeight(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          SizedBox(
            width: 24,
            child: Column(
              children: [
                const SizedBox(height: 4),
                Container(
                  width: 12,
                  height: 12,
                  decoration: BoxDecoration(color: cor, shape: BoxShape.circle),
                ),
                if (!ultima) Expanded(child: Container(width: 2, color: context.cores.linha)),
              ],
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Padding(
              padding: EdgeInsets.only(bottom: ultima ? 0 : 16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    registro.para.rotulo(context.textos),
                    style: tema.textTheme.bodyLarge?.copyWith(fontWeight: FontWeight.w600),
                  ),
                  Text(
                    context.dataHora(registro.em),
                    style: tema.textTheme.bodySmall?.copyWith(
                      color: tema.colorScheme.onSurfaceVariant,
                    ),
                  ),
                  if (registro.justificativa != null) ...[
                    const SizedBox(height: 4),
                    Text(registro.justificativa!),
                  ],
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
