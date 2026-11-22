import 'dart:io';

import 'package:material_ui/material_ui.dart';

import '../../../../core/apresentacao/contexto.dart';
import '../../domain/arquivo_evidencia.dart';
import '../../domain/portas.dart';

const _ladoMiniatura = 72.0;

/// Fotos escolhidas no formulário, ainda não enviadas, com botões de câmera e galeria.
class PainelEvidencias extends StatelessWidget {
  const PainelEvidencias({
    required this.arquivos,
    required this.aoAdicionar,
    required this.aoRemover,
    super.key,
  });

  final List<ArquivoEvidencia> arquivos;
  final void Function(OrigemImagem) aoAdicionar;
  final void Function(ArquivoEvidencia) aoRemover;

  @override
  Widget build(BuildContext context) {
    final t = context.textos;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          t.ajudaEvidencias(maximoEvidenciasPorOcorrencia),
          style: Theme.of(context).textTheme.bodySmall,
        ),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [for (final arquivo in arquivos) _miniatura(context, arquivo)],
        ),
        const SizedBox(height: 8),
        Row(
          children: [
            OutlinedButton.icon(
              onPressed: () => aoAdicionar(OrigemImagem.camera),
              icon: const Icon(Icons.photo_camera_outlined),
              label: Text(t.tirarFoto),
            ),
            const SizedBox(width: 8),
            OutlinedButton.icon(
              onPressed: () => aoAdicionar(OrigemImagem.galeria),
              icon: const Icon(Icons.photo_library_outlined),
              label: Text(t.escolherGaleria),
            ),
          ],
        ),
      ],
    );
  }

  Widget _miniatura(BuildContext context, ArquivoEvidencia arquivo) => Stack(
    children: [
      ClipRRect(
        borderRadius: BorderRadius.circular(8),
        child: arquivo.formato == FormatoEvidencia.pdf
            ? const SizedBox.square(dimension: _ladoMiniatura, child: Icon(Icons.picture_as_pdf))
            : Image.file(
                File(arquivo.caminho),
                width: _ladoMiniatura,
                height: _ladoMiniatura,
                fit: BoxFit.cover,
              ),
      ),
      Positioned(
        right: 0,
        top: 0,
        child: IconButton.filledTonal(
          visualDensity: VisualDensity.compact,
          tooltip: context.textos.remover,
          onPressed: () => aoRemover(arquivo),
          icon: const Icon(Icons.close, size: 16),
        ),
      ),
    ],
  );
}
