import 'package:riverpod/riverpod.dart';

import '../domain/arquivo_evidencia.dart';
import '../domain/ocorrencia.dart';
import 'dependencias.dart';

final detalheOcorrenciaProvider =
    AsyncNotifierProvider.family<DetalheOcorrencia, OcorrenciaDetalhe, String>(
      DetalheOcorrencia.new,
      isAutoDispose: true,
    );

/// Detalhe de uma ocorrência e os atos do Agente autor sobre ela.
class DetalheOcorrencia extends AsyncNotifier<OcorrenciaDetalhe> {
  DetalheOcorrencia(this.ocorrenciaId);

  final String ocorrenciaId;

  @override
  Future<OcorrenciaDetalhe> build() => ref.read(repositorioOcorrenciasProvider).obter(ocorrenciaId);

  /// Aplica a versão já devolvida pelo backend (ex.: após corrigir), sem nova requisição.
  void atualizarCom(OcorrenciaDetalhe ocorrencia) => state = AsyncData(ocorrencia);

  /// Devolve a ocorrência corrigida à fila do Delegado. Lança `Falha` se recusado.
  Future<void> reenviar() async {
    final atualizada = await ref.read(repositorioOcorrenciasProvider).reenviar(ocorrenciaId);
    state = AsyncData(atualizada);
  }

  /// Anexa uma foto avulsa; lança [EvidenciaInvalida] ou `Falha`.
  Future<void> anexar(ArquivoEvidencia arquivo) async {
    final atual = state.value;
    final erro = validarLoteEvidencias([arquivo], jaAnexadas: atual?.evidencias.length ?? 0);
    if (erro != null) throw EvidenciaInvalida(erro);
    final repositorio = ref.read(repositorioOcorrenciasProvider);
    await repositorio.anexarEvidencia(ocorrenciaId, arquivo);
    state = AsyncData(await repositorio.obter(ocorrenciaId));
  }
}
