import 'dart:typed_data';

import 'package:riverpod/riverpod.dart';

import 'dependencias.dart';

typedef ReferenciaEvidencia = ({String ocorrenciaId, String evidenciaId});

/// Bytes da evidência, baixados sob demanda e descartados ao fechar a visualização.
final conteudoEvidenciaProvider = FutureProvider.autoDispose.family<Uint8List, ReferenciaEvidencia>(
  (ref, evidencia) => ref
      .watch(repositorioOcorrenciasProvider)
      .baixarEvidencia(evidencia.ocorrenciaId, evidencia.evidenciaId),
);
