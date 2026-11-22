import 'package:dio/dio.dart';

import '../../../core/http/falhas_http.dart';
import '../../../core/http/json.dart';
import '../../ocorrencias/data/ocorrencia_mapper.dart';
import '../../ocorrencias/domain/ocorrencia.dart';
import '../domain/decisao_revisao.dart';
import '../domain/portas.dart';

/// Decisões do Delegado em `backend/src/adapters/inbound/http/v1/revisao_router.py`.
final class RepositorioRevisaoHttp implements RepositorioRevisao {
  RepositorioRevisaoHttp(this._http);

  final Dio _http;

  @override
  Future<OcorrenciaDetalhe> decidir(String ocorrenciaId, DecisaoRevisao decisao) =>
      comFalhasTraduzidas(() async {
        final (acao, corpo) = _requisicao(decisao);
        final resposta = await _http.post<Json>('/v1/ocorrencias/$ocorrenciaId/$acao', data: corpo);
        return OcorrenciaMapper.detalheDeJson(resposta.data!);
      });

  static (String, Json) _requisicao(DecisaoRevisao decisao) => switch (decisao) {
    Validar(:final despacho) => (
      'validar',
      {if (despacho != null && despacho.trim().isNotEmpty) 'despacho': despacho.trim()},
    ),
    Devolver(:final justificativa) => ('devolver', {'justificativa': justificativa.trim()}),
    Rejeitar(:final justificativa) => ('rejeitar', {'justificativa': justificativa.trim()}),
  };
}
