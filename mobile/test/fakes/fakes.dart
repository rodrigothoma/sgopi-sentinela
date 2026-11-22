import 'dart:typed_data';

import 'package:sgopi_mobile/core/dominio/falha.dart';
import 'package:sgopi_mobile/core/dominio/pagina.dart';
import 'package:sgopi_mobile/core/dominio/relogio.dart';
import 'package:sgopi_mobile/features/autenticacao/domain/portas.dart';
import 'package:sgopi_mobile/features/notificacoes/domain/notificacao.dart';
import 'package:sgopi_mobile/features/notificacoes/domain/portas.dart';
import 'package:sgopi_mobile/features/autenticacao/domain/sessao.dart';
import 'package:sgopi_mobile/features/ocorrencias/data/ocorrencia_mapper.dart';
import 'package:sgopi_mobile/features/ocorrencias/domain/arquivo_evidencia.dart';
import 'package:sgopi_mobile/features/ocorrencias/domain/dados_ocorrencia.dart';
import 'package:sgopi_mobile/features/ocorrencias/domain/enums.dart';
import 'package:sgopi_mobile/features/ocorrencias/domain/ocorrencia.dart';
import 'package:sgopi_mobile/features/ocorrencias/domain/portas.dart';
import 'package:sgopi_mobile/features/preferencias/domain/portas.dart';
import 'package:sgopi_mobile/features/preferencias/domain/preferencias.dart';
import 'package:sgopi_mobile/features/revisao/domain/decisao_revisao.dart';
import 'package:sgopi_mobile/features/revisao/domain/portas.dart';

import 'exemplos.dart';

/// Dentro de [RelogioFixo], `agora` é o próprio método; o instante de referência vem daqui.
final _instanteReferencia = agora;

final class RelogioFixo implements Relogio {
  RelogioFixo([DateTime? instante]) : instante = instante ?? _instanteReferencia;

  DateTime instante;

  @override
  DateTime agora() => instante;
}

final class ArmazenamentoSessaoMemoria implements ArmazenamentoSessao {
  ArmazenamentoSessaoMemoria([this.sessao]);

  Sessao? sessao;

  @override
  Future<Sessao?> carregar() async => sessao;

  @override
  Future<void> salvar(Sessao sessao) async => this.sessao = sessao;

  @override
  Future<void> limpar() async => sessao = null;
}

final class RepositorioAutenticacaoFake implements RepositorioAutenticacao {
  /// Login aceito -> sessão; ausente -> credenciais inválidas.
  final Map<String, Sessao> usuarios = {};

  @override
  Future<Sessao> entrar({required String login, required String senha}) async {
    final sessao = usuarios[login];
    if (sessao == null || senha != 'Senha@123') {
      throw const Falha(
        TipoFalha.naoAutenticado,
        detalhe: 'Credenciais inválidas.',
        codigo: 'auth.credenciais_invalidas',
        requestId: 'abcdef1234567890',
      );
    }
    return sessao;
  }
}

/// Repositório em memória com registro das chamadas, para casos de uso e telas.
final class RepositorioOcorrenciasFake implements RepositorioOcorrencias {
  RepositorioOcorrenciasFake({List<OcorrenciaDetalhe>? ocorrencias})
    : ocorrencias = {for (final o in ocorrencias ?? <OcorrenciaDetalhe>[]) o.id: o};

  final Map<String, OcorrenciaDetalhe> ocorrencias;
  final List<DadosOcorrencia> registradas = [];
  final List<(String, DadosOcorrencia)> correcoes = [];
  final List<(String, ArquivoEvidencia)> anexos = [];
  final List<(FiltroOcorrencias, int, int)> consultas = [];

  /// Nomes de arquivo que o "backend" recusa no upload.
  final Set<String> anexosRecusados = {};
  Falha? falhaNaListagem;

  /// Conteúdo devolvido no download; uma [Falha] aqui é lançada.
  Object conteudoEvidencia = pngMinimo;
  final List<(String, String)> downloads = [];

  @override
  Future<Pagina<OcorrenciaResumo>> listar(
    FiltroOcorrencias filtro, {
    required int limite,
    required int deslocamento,
  }) async {
    consultas.add((filtro, limite, deslocamento));
    if (falhaNaListagem case final falha?) throw falha;
    final todos = ocorrencias.values
        .where((o) => filtro.status.isEmpty || filtro.status.contains(o.status))
        .toList();
    return Pagina(
      itens: todos.skip(deslocamento).take(limite).toList(),
      total: todos.length,
      limite: limite,
      deslocamento: deslocamento,
    );
  }

  @override
  Future<OcorrenciaDetalhe> obter(String ocorrenciaId) async =>
      ocorrencias[ocorrenciaId] ?? (throw const Falha(TipoFalha.naoEncontrado));

  @override
  Future<ProtocoloRegistrado> registrar(DadosOcorrencia dados) async {
    registradas.add(dados);
    final id = 'oc-nova-${registradas.length}';
    ocorrencias[id] = OcorrenciaMapper.detalheDeJson(detalheJson(id: id));
    return ProtocoloRegistrado(
      ocorrenciaId: id,
      numeroProtocolo: 'BO-2026-000999',
      status: StatusOcorrencia.aguardandoRevisao,
      criadaEm: agora,
    );
  }

  @override
  Future<OcorrenciaDetalhe> corrigir(String ocorrenciaId, DadosOcorrencia dados) async {
    correcoes.add((ocorrenciaId, dados));
    return obter(ocorrenciaId);
  }

  @override
  Future<OcorrenciaDetalhe> reenviar(String ocorrenciaId) async {
    final json = detalheJson(id: ocorrenciaId, status: 'AGUARDANDO_REVISAO');
    return ocorrencias[ocorrenciaId] = OcorrenciaMapper.detalheDeJson(json);
  }

  @override
  Future<Evidencia> anexarEvidencia(String ocorrenciaId, ArquivoEvidencia arquivo) async {
    if (anexosRecusados.contains(arquivo.nome)) {
      throw const Falha(TipoFalha.validacao, codigo: 'evidencia.conteudo_invalido');
    }
    anexos.add((ocorrenciaId, arquivo));
    return Evidencia(
      id: 'ev-${anexos.length}',
      nomeOriginal: arquivo.nome,
      formato: 'jpeg',
      tamanhoBytes: arquivo.tamanhoBytes,
      hashSha256: 'a' * 64,
      enviadaEm: agora,
    );
  }

  @override
  Future<Uint8List> baixarEvidencia(String ocorrenciaId, String evidenciaId) async {
    downloads.add((ocorrenciaId, evidenciaId));
    return switch (conteudoEvidencia) {
      final Uint8List bytes => bytes,
      final Object erro => throw erro,
    };
  }
}

final class RepositorioRevisaoFake implements RepositorioRevisao {
  final List<(String, DecisaoRevisao)> decisoes = [];

  @override
  Future<OcorrenciaDetalhe> decidir(String ocorrenciaId, DecisaoRevisao decisao) async {
    decisoes.add((ocorrenciaId, decisao));
    final status = switch (decisao) {
      Validar() => 'VALIDADA',
      Devolver() => 'EM_CORRECAO',
      Rejeitar() => 'REJEITADA',
    };
    return OcorrenciaMapper.detalheDeJson(detalheJson(id: ocorrenciaId, status: status));
  }
}

final class LocalizacaoFake implements PortaLocalizacao {
  LocalizacaoFake([this.resultado = const Coordenada(latitude: -29.78, longitude: -55.79)]);

  Object resultado;

  @override
  Future<Coordenada> obterAtual() async => switch (resultado) {
    final Coordenada c => c,
    final Object erro => throw erro,
  };
}

final class SeletorImagemFake implements PortaSeletorImagem {
  ArquivoEvidencia? proxima;

  @override
  Future<ArquivoEvidencia?> selecionar(OrigemImagem origem) async => proxima;
}

final class ArmazenamentoPreferenciasMemoria implements ArmazenamentoPreferencias {
  ArmazenamentoPreferenciasMemoria([this.preferencias = const Preferencias()]);

  Preferencias preferencias;
  int gravacoes = 0;

  @override
  Preferencias carregar() => preferencias;

  @override
  Future<void> salvar(Preferencias preferencias) async {
    gravacoes++;
    this.preferencias = preferencias;
  }
}

/// Notificações em memória; [falhaAoMarcar] simula o backend recusando a marcação.
final class RepositorioNotificacoesFake implements RepositorioNotificacoes {
  final List<Notificacao> itens = [];
  final List<String> marcadas = [];
  final List<(int, int)> consultas = [];
  int marcarTodasChamadas = 0;
  Falha? falhaAoMarcar;

  @override
  Future<LoteNotificacoes> listar({required int limite, required int deslocamento}) async {
    consultas.add((limite, deslocamento));
    return LoteNotificacoes(
      itens: itens.skip(deslocamento).take(limite).toList(),
      naoLidas: await contarNaoLidas(),
    );
  }

  @override
  Future<int> contarNaoLidas() async => itens.where((n) => !n.lida).length;

  @override
  Future<void> marcarLida(String notificacaoId) async {
    if (falhaAoMarcar case final falha?) throw falha;
    marcadas.add(notificacaoId);
    final i = itens.indexWhere((n) => n.id == notificacaoId);
    if (i >= 0) itens[i] = itens[i].marcadaComoLida();
  }

  @override
  Future<void> marcarTodasLidas() async {
    marcarTodasChamadas++;
    for (var i = 0; i < itens.length; i++) {
      itens[i] = itens[i].marcadaComoLida();
    }
  }
}
