import 'dart:typed_data';

import 'package:dio/dio.dart';

import '../../../core/dominio/pagina.dart';
import '../../../core/http/falhas_http.dart';
import '../../../core/http/json.dart';
import '../domain/arquivo_evidencia.dart';
import '../domain/dados_ocorrencia.dart';
import '../domain/ocorrencia.dart';
import '../domain/portas.dart';
import 'ocorrencia_mapper.dart';

const _base = '/v1/ocorrencias';

final class RepositorioOcorrenciasHttp implements RepositorioOcorrencias {
  RepositorioOcorrenciasHttp(this._http);

  final Dio _http;

  @override
  Future<Pagina<OcorrenciaResumo>> listar(
    FiltroOcorrencias filtro, {
    required int limite,
    required int deslocamento,
  }) => comFalhasTraduzidas(() async {
    final resposta = await _http.get<Json>(
      _base,
      queryParameters: {
        'limit': limite,
        'offset': deslocamento,
        if (filtro.status.isNotEmpty) 'status': [for (final s in filtro.status) s.codigo],
        if (filtro.somenteMinhas) 'somente_minhas': true,
        if (filtro.maisRecentesPrimeiro) 'mais_recentes_primeiro': true,
        if (filtro.ordenarPorPrioridade) 'ordenar_por_prioridade': true,
      },
    );
    return OcorrenciaMapper.paginaDeJson(resposta.data!);
  });

  @override
  Future<OcorrenciaDetalhe> obter(String ocorrenciaId) => comFalhasTraduzidas(() async {
    final resposta = await _http.get<Json>('$_base/$ocorrenciaId');
    return OcorrenciaMapper.detalheDeJson(resposta.data!);
  });

  @override
  Future<ProtocoloRegistrado> registrar(DadosOcorrencia dados) => comFalhasTraduzidas(() async {
    final resposta = await _http.post<Json>(_base, data: OcorrenciaMapper.registroParaJson(dados));
    return OcorrenciaMapper.protocoloDeJson(resposta.data!);
  });

  @override
  Future<OcorrenciaDetalhe> corrigir(String ocorrenciaId, DadosOcorrencia dados) =>
      comFalhasTraduzidas(() async {
        final resposta = await _http.put<Json>(
          '$_base/$ocorrenciaId',
          data: OcorrenciaMapper.correcaoParaJson(dados),
        );
        return OcorrenciaMapper.detalheDeJson(resposta.data!);
      });

  @override
  Future<OcorrenciaDetalhe> reenviar(String ocorrenciaId) => comFalhasTraduzidas(() async {
    final resposta = await _http.post<Json>('$_base/$ocorrenciaId/reenviar');
    return OcorrenciaMapper.detalheDeJson(resposta.data!);
  });

  /// Multipart com o campo `arquivo`; o backend confere extensão, MIME e assinatura do conteúdo.
  @override
  Future<Evidencia> anexarEvidencia(String ocorrenciaId, ArquivoEvidencia arquivo) =>
      comFalhasTraduzidas(() async {
        final formato = arquivo.formato;
        if (formato == null) throw const EvidenciaInvalida(ErroEvidencia.formatoNaoSuportado);
        final corpo = FormData.fromMap({
          'arquivo': await MultipartFile.fromFile(
            arquivo.caminho,
            filename: arquivo.nome,
            contentType: DioMediaType.parse(formato.tipoMime),
          ),
        });
        final resposta = await _http.post<Json>('$_base/$ocorrenciaId/evidencias', data: corpo);
        return OcorrenciaMapper.evidenciaDeJson(resposta.data!);
      });

  @override
  Future<Uint8List> baixarEvidencia(String ocorrenciaId, String evidenciaId) =>
      comFalhasTraduzidas(() async {
        final resposta = await _http.get<List<int>>(
          '$_base/$ocorrenciaId/evidencias/$evidenciaId/download',
          options: Options(responseType: ResponseType.bytes),
        );
        return Uint8List.fromList(resposta.data!);
      });
}
