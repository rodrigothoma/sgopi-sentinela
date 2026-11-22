import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:material_ui/material_ui.dart';

import '../../../core/apresentacao/contexto.dart';
import '../../../core/apresentacao/rotas.dart';
import '../application/dependencias.dart';
import '../application/lista_ocorrencias.dart';
import '../application/registrar_ocorrencia.dart';
import '../domain/arquivo_evidencia.dart';
import '../domain/dados_ocorrencia.dart';
import 'widgets/formulario_ocorrencia.dart';

/// UC01: registro da ocorrência pelo Agente em campo.
class TelaRegistrarOcorrencia extends ConsumerWidget {
  const TelaRegistrarOcorrencia({super.key});

  Future<void> _registrar(
    BuildContext context,
    WidgetRef ref,
    DadosOcorrencia dados,
    List<ArquivoEvidencia> evidencias,
  ) async {
    final resultado = await ref.read(registrarOcorrenciaProvider).executar(dados, evidencias);
    ref.invalidate(listaOcorrenciasProvider);
    // O envio termina aqui (o formulário sai do estado "enviando"); o comprovante vem depois.
    if (context.mounted) unawaited(_concluir(context, resultado));
  }

  Future<void> _concluir(BuildContext context, ResultadoRegistro resultado) async {
    await _mostrarComprovante(context, resultado);
    if (!context.mounted) return;
    context.pushReplacement(Rotas.detalheOcorrencia(resultado.protocolo.ocorrenciaId));
  }

  Future<void> _mostrarComprovante(BuildContext context, ResultadoRegistro resultado) {
    final t = context.textos;
    final naoEnviadas = resultado.evidenciasNaoEnviadas.length;
    return showDialog<void>(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        icon: const Icon(Icons.check_circle_outline),
        title: Text(t.registroConcluidoTitulo),
        content: Text(
          [
            t.registroConcluidoMensagem(resultado.protocolo.numeroProtocolo),
            if (naoEnviadas > 0) t.evidenciasNaoEnviadas(naoEnviadas),
          ].join('\n\n'),
        ),
        actions: [FilledButton(onPressed: () => Navigator.of(context).pop(), child: Text(t.ok))],
      ),
    );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) => FormularioOcorrencia(
    titulo: context.textos.registrarTitulo,
    rotuloEnviar: context.textos.enviarRegistro,
    aoEnviar: (dados, evidencias) => _registrar(context, ref, dados, evidencias),
  );
}
