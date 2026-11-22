import 'package:image_picker/image_picker.dart';

import '../domain/arquivo_evidencia.dart';
import '../domain/portas.dart';

/// Lado maior e qualidade JPEG: mantém a foto legível e bem abaixo do limite de 10 MB.
const _ladoMaximoPixels = 2560.0;
const _qualidadeJpeg = 85;

/// Câmera e galeria via `image_picker`. A validação de formato fica no domínio.
final class SeletorImagemImagePicker implements PortaSeletorImagem {
  SeletorImagemImagePicker([ImagePicker? seletor]) : _seletor = seletor ?? ImagePicker();

  final ImagePicker _seletor;

  @override
  Future<ArquivoEvidencia?> selecionar(OrigemImagem origem) async {
    final foto = await _seletor.pickImage(
      source: origem == OrigemImagem.camera ? ImageSource.camera : ImageSource.gallery,
      maxWidth: _ladoMaximoPixels,
      maxHeight: _ladoMaximoPixels,
      imageQuality: _qualidadeJpeg,
      requestFullMetadata: false,
    );
    if (foto == null) return null;
    return ArquivoEvidencia(caminho: foto.path, nome: foto.name, tamanhoBytes: await foto.length());
  }
}
