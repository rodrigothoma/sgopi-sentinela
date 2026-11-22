import 'dart:convert';

import 'package:sgopi_mobile/features/autenticacao/domain/papel.dart';
import 'package:sgopi_mobile/features/autenticacao/domain/sessao.dart';
import 'package:sgopi_mobile/features/autenticacao/domain/usuario.dart';
import 'package:sgopi_mobile/features/ocorrencias/domain/arquivo_evidencia.dart';
import 'package:sgopi_mobile/features/ocorrencias/domain/dados_ocorrencia.dart';
import 'package:sgopi_mobile/features/ocorrencias/domain/enums.dart';
import 'package:sgopi_mobile/features/ocorrencias/domain/ocorrencia.dart';

final agora = DateTime.utc(2026, 11, 22, 15);

/// PNG válido de 1×1 pixel, para o download de evidências.
final pngMinimo = base64Decode(
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==',
);

Sessao sessaoDe(Papel papel, {DateTime? expiraEm}) => Sessao(
  token: 'jwt-${papel.codigo}',
  expiraEm: expiraEm ?? agora.add(const Duration(hours: 8)),
  usuario: Usuario(id: 'u-${papel.codigo}', nome: 'Fulano', login: papel.codigo, papel: papel),
);

DadosOcorrencia dadosValidos({List<Envolvido>? envolvidos, String? descricao}) => DadosOcorrencia(
  natureza: 'Furto',
  descricao: descricao ?? 'Subtração de celular na saída do mercado municipal.',
  localizacao: 'Rua Andradas, 100 - Alegrete',
  coordenada: const Coordenada(latitude: -29.78, longitude: -55.79),
  dataHoraFato: agora.subtract(const Duration(hours: 1)),
  envolvidos: envolvidos ?? const [Envolvido(nome: 'Maria Silva', tipo: TipoEnvolvido.vitima)],
);

ArquivoEvidencia foto({String nome = 'foto.jpg', int tamanho = 2048}) =>
    ArquivoEvidencia(caminho: '/tmp/$nome', nome: nome, tamanhoBytes: tamanho);

/// JSON no formato de `OcorrenciaDetalheSchema` do backend.
Map<String, dynamic> detalheJson({
  String id = 'oc-1',
  String status = 'AGUARDANDO_REVISAO',
  int evidencias = 0,
}) => {
  'ocorrencia_id': id,
  'numero_protocolo': 'BO-2026-000123',
  'natureza': 'Furto',
  'localizacao': 'Rua Andradas, 100 - Alegrete',
  'latitude': -29.78,
  'longitude': -55.79,
  'status': status,
  'data_hora_fato': '2026-11-22T14:00:00+00:00',
  'criada_em': '2026-11-22T14:30:00+00:00',
  'atualizada_em': '2026-11-22T14:30:00+00:00',
  'agente_policial_id': 'u-AGENTE',
  'versao': 1,
  'inquerito_id': null,
  'origem': 'POLICIAL',
  'prioridade': 'ALTA',
  'descricao': 'Subtração de celular na saída do mercado municipal.',
  'validada_por_id': null,
  'justificativa_revisao': null,
  'desfecho': null,
  'hash_narrativa': null,
  'narrativa_integra': null,
  'chave_autenticidade': null,
  'arquivada_por_id': null,
  'motivo_arquivamento': null,
  'excluida_por_id': null,
  'motivo_exclusao': null,
  'envolvidos': [
    {
      'id': 'e-1',
      'nome': 'Maria Silva',
      'tipo': 'VITIMA',
      'documento': null,
      'email': null,
      'telefone': null,
    },
  ],
  'tipificacoes': [
    {'artigo': 'Art. 155 CP', 'descricao': 'Furto simples'},
  ],
  'evidencias': [
    for (var i = 0; i < evidencias; i++)
      {
        'id': 'ev-$i',
        'nome_original': 'foto$i.jpg',
        'formato': 'jpeg',
        'tamanho': 1024,
        'hash_sha256': 'a' * 64,
        'enviada_em': '2026-11-22T14:31:00+00:00',
      },
  ],
  'itens_apreendidos': <Object>[],
  'historico_status': [
    {
      'de': null,
      'para': 'AGUARDANDO_REVISAO',
      'em': '2026-11-22T14:30:00+00:00',
      'por_id': 'u-AGENTE',
      'justificativa': null,
    },
  ],
};
