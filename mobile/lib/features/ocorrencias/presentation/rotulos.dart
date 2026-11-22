import 'package:material_ui/material_ui.dart';

import '../../../core/apresentacao/design/cores_sgopi.dart';
import '../../../core/apresentacao/mensagem_falha.dart';
import '../../../core/dominio/falha.dart';
import '../../../core/l10n/gerado/textos.dart';
import '../domain/arquivo_evidencia.dart';
import '../domain/dados_ocorrencia.dart';
import '../domain/enums.dart';
import '../domain/portas.dart';

extension RotuloStatus on StatusOcorrencia {
  String rotulo(Textos t) => switch (this) {
    StatusOcorrencia.aguardandoRevisao => t.statusAguardandoRevisao,
    StatusOcorrencia.emCorrecao => t.statusEmCorrecao,
    StatusOcorrencia.rejeitada => t.statusRejeitada,
    StatusOcorrencia.validada => t.statusValidada,
    StatusOcorrencia.emAtendimento => t.statusEmAtendimento,
    StatusOcorrencia.encerrada => t.statusEncerrada,
    StatusOcorrencia.arquivada => t.statusArquivada,
    StatusOcorrencia.excluida => t.statusExcluida,
  };

  /// Cores de `.status-*` em `frontend/src/styles.css`.
  Color cor(CoresSgopi c) => switch (this) {
    StatusOcorrencia.aguardandoRevisao => c.aviso,
    StatusOcorrencia.emCorrecao => c.correcao,
    StatusOcorrencia.validada => c.sucesso,
    StatusOcorrencia.emAtendimento => c.informacao,
    StatusOcorrencia.rejeitada || StatusOcorrencia.excluida => c.perigo,
    StatusOcorrencia.encerrada || StatusOcorrencia.arquivada => c.neutro,
  };
}

extension RotuloPrioridade on PrioridadeOcorrencia {
  String rotulo(Textos t) => switch (this) {
    PrioridadeOcorrencia.urgente => t.prioridadeUrgente,
    PrioridadeOcorrencia.alta => t.prioridadeAlta,
    PrioridadeOcorrencia.media => t.prioridadeMedia,
    PrioridadeOcorrencia.baixa => t.prioridadeBaixa,
  };

  /// Marcador do web (`.prioridade-*`): a cor nunca é o único sinal.
  String get simbolo => switch (this) {
    PrioridadeOcorrencia.urgente => '▲▲',
    PrioridadeOcorrencia.alta => '▲',
    PrioridadeOcorrencia.media => '■',
    PrioridadeOcorrencia.baixa => '▼',
  };

  Color cor(CoresSgopi c) => switch (this) {
    PrioridadeOcorrencia.urgente => c.urgente,
    PrioridadeOcorrencia.alta => c.alta,
    PrioridadeOcorrencia.media || PrioridadeOcorrencia.baixa => c.neutro,
  };
}

extension RotuloTipoEnvolvido on TipoEnvolvido {
  String rotulo(Textos t) => switch (this) {
    TipoEnvolvido.vitima => t.tipoVitima,
    TipoEnvolvido.testemunha => t.tipoTestemunha,
    TipoEnvolvido.suspeito => t.tipoSuspeito,
    TipoEnvolvido.comunicante => t.tipoComunicante,
  };
}

String mensagemErroOcorrencia(Textos t, ErroOcorrencia erro) => switch (erro) {
  ErroOcorrencia.naturezaVazia => t.erroNaturezaVazia,
  ErroOcorrencia.descricaoCurta => t.erroDescricaoCurta(tamanhoMinimoDescricao),
  ErroOcorrencia.localizacaoVazia => t.erroLocalizacaoVazia,
  ErroOcorrencia.coordenadaInvalida => t.erroCoordenadaInvalida,
  ErroOcorrencia.dataFatoFutura => t.erroDataFutura,
  ErroOcorrencia.semEnvolvidos => t.erroSemEnvolvidos,
};

String mensagemErroEnvolvido(Textos t, ErroEnvolvido erro) => switch (erro) {
  ErroEnvolvido.nomeVazio => t.erroNomeVazio,
  ErroEnvolvido.nomeComNumeros => t.erroNomeComNumeros,
  ErroEnvolvido.documentoInvalido => t.erroDocumentoInvalido,
};

String mensagemErroEvidencia(Textos t, ErroEvidencia erro) => switch (erro) {
  ErroEvidencia.formatoNaoSuportado => t.erroFormatoEvidencia,
  ErroEvidencia.arquivoVazio => t.erroArquivoVazio,
  ErroEvidencia.tamanhoExcedido => t.erroTamanhoEvidencia,
  ErroEvidencia.limiteAtingido => t.erroLimiteEvidencias(maximoEvidenciasPorOcorrencia),
};

String mensagemLocalizacao(Textos t, MotivoLocalizacaoIndisponivel motivo) => switch (motivo) {
  MotivoLocalizacaoIndisponivel.servicoDesligado => t.erroLocalizacaoServico,
  MotivoLocalizacaoIndisponivel.permissaoNegada => t.erroLocalizacaoPermissao,
  MotivoLocalizacaoIndisponivel.falhaLeitura => t.erroLocalizacaoLeitura,
};

/// Mensagem para qualquer erro lançado pelos fluxos de ocorrência.
String mensagemDeErro(Textos t, Object erro) => switch (erro) {
  Falha() => mensagemDeFalha(t, erro),
  EvidenciaInvalida(:final erro) => mensagemErroEvidencia(t, erro),
  LocalizacaoIndisponivel(:final motivo) => mensagemLocalizacao(t, motivo),
  DadosOcorrenciaInvalidos(:final erros) =>
    erros.map((e) => mensagemErroOcorrencia(t, e)).join('\n'),
  _ => t.erroInesperado,
};
