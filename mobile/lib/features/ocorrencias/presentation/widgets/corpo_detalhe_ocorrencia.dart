import 'package:material_ui/material_ui.dart';

import '../../../../core/apresentacao/contexto.dart';
import '../../../../core/apresentacao/secao.dart';
import '../../domain/ocorrencia.dart';
import '../rotulos.dart';
import '../tela_evidencia.dart';
import 'selo_status.dart';

/// Leitura completa da ocorrência, compartilhada pelo detalhe do Agente e pela revisão do Delegado.
class CorpoDetalheOcorrencia extends StatelessWidget {
  const CorpoDetalheOcorrencia(this.ocorrencia, {super.key});

  final OcorrenciaDetalhe ocorrencia;

  @override
  Widget build(BuildContext context) {
    final t = context.textos;
    final o = ocorrencia;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _cabecalho(context),
        if (o.justificativaRevisao != null) _justificativa(context, o.justificativaRevisao!),
        TituloSecao(t.rotuloDescricao),
        SelectableText(o.descricao),
        TituloSecao(t.secaoEnvolvidos),
        ..._ouNenhum(context, [
          for (final e in o.envolvidos)
            _linha(Icons.person_outline, e.nome, [e.tipo.rotulo(t), ?e.documento].join(' · ')),
        ]),
        TituloSecao(t.secaoTipificacoes),
        ..._ouNenhum(context, [
          for (final tp in o.tipificacoes) _linha(Icons.gavel_outlined, tp.artigo, tp.descricao),
        ]),
        TituloSecao(t.secaoEvidencias),
        ..._ouNenhum(context, [for (final ev in o.evidencias) _evidencia(context, ev)]),
        TituloSecao(t.rotuloHistorico),
        for (final h in o.historico.reversed)
          _linha(
            Icons.history,
            h.para.rotulo(t),
            [context.dataHora(h.em), ?h.justificativa].join('\n'),
          ),
        if (o.hashNarrativa != null) ...[
          TituloSecao(t.rotuloHashNarrativa),
          SelectableText(o.hashNarrativa!, style: const TextStyle(fontFamily: 'monospace')),
        ],
      ],
    );
  }

  Widget _cabecalho(BuildContext context) {
    final t = context.textos;
    final tema = Theme.of(context).textTheme;
    final o = ocorrencia;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(child: Text(o.numeroProtocolo, style: tema.labelLarge)),
            SeloStatus(o.status),
          ],
        ),
        const SizedBox(height: 8),
        Text(o.natureza, style: tema.headlineSmall),
        Text('${t.campoPrioridade}: ${o.prioridade.rotulo(t)}'),
        Text('${t.rotuloFato}: ${context.dataHora(o.dataHoraFato)}'),
        Text('${t.rotuloRegistradaEm}: ${context.dataHora(o.criadaEm)}'),
        const SizedBox(height: 4),
        Text(o.localizacao),
        Text(
          t.coordenadaDefinida(
            o.coordenada.latitude.toStringAsFixed(6),
            o.coordenada.longitude.toStringAsFixed(6),
          ),
          style: tema.bodySmall,
        ),
      ],
    );
  }

  Widget _justificativa(BuildContext context, String texto) {
    final cores = Theme.of(context).colorScheme;
    return Card(
      color: cores.errorContainer,
      margin: const EdgeInsets.only(top: 16),
      child: ListTile(
        leading: Icon(Icons.feedback_outlined, color: cores.onErrorContainer),
        title: Text(context.textos.rotuloJustificativaDelegado),
        subtitle: Text(texto),
        textColor: cores.onErrorContainer,
      ),
    );
  }

  /// Fotos abrem em tela cheia; PDF ainda não tem visualizador no app.
  Widget _evidencia(BuildContext context, Evidencia evidencia) {
    final t = context.textos;
    final data = context.dataHora(evidencia.enviadaEm);
    if (!evidencia.ehImagem) {
      return _linha(
        Icons.picture_as_pdf_outlined,
        evidencia.nomeOriginal,
        '$data\n${t.pdfSomenteWeb}',
      );
    }
    return ListTile(
      key: Key('evidencia.${evidencia.id}'),
      dense: true,
      contentPadding: EdgeInsets.zero,
      leading: const Icon(Icons.image_outlined),
      title: Text(evidencia.nomeOriginal),
      subtitle: Text(data),
      trailing: Icon(Icons.zoom_in, semanticLabel: t.verEvidencia),
      onTap: () => abrirEvidencia(context, ocorrencia.id, evidencia),
    );
  }

  Widget _linha(IconData icone, String titulo, String subtitulo) => ListTile(
    dense: true,
    contentPadding: EdgeInsets.zero,
    leading: Icon(icone),
    title: Text(titulo),
    subtitle: subtitulo.isEmpty ? null : Text(subtitulo),
  );

  List<Widget> _ouNenhum(BuildContext context, List<Widget> itens) =>
      itens.isEmpty ? [Text(context.textos.nenhumItem)] : itens;
}
