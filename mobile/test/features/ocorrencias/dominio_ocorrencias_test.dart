import 'package:flutter_test/flutter_test.dart';
import 'package:sgopi_mobile/features/ocorrencias/domain/arquivo_evidencia.dart';
import 'package:sgopi_mobile/features/ocorrencias/domain/dados_ocorrencia.dart';
import 'package:sgopi_mobile/features/ocorrencias/domain/enums.dart';
import 'package:sgopi_mobile/features/ocorrencias/domain/ocorrencia.dart';

import '../../fakes/exemplos.dart';

void main() {
  group('DadosOcorrencia.validar', () {
    test('dados completos são aceitos', () {
      expect(dadosValidos().validar(agora), isEmpty);
    });

    test('aponta cada regra violada do UC01', () {
      final dados = DadosOcorrencia(
        natureza: ' ',
        descricao: 'curta',
        localizacao: '',
        coordenada: const Coordenada(latitude: 91, longitude: 0),
        dataHoraFato: agora.add(const Duration(minutes: 1)),
        envolvidos: const [],
      );
      expect(dados.validar(agora), {
        ErroOcorrencia.naturezaVazia,
        ErroOcorrencia.descricaoCurta,
        ErroOcorrencia.localizacaoVazia,
        ErroOcorrencia.coordenadaInvalida,
        ErroOcorrencia.dataFatoFutura,
        ErroOcorrencia.semEnvolvidos,
      });
    });

    test('descrição conta caracteres sem os espaços das pontas', () {
      final descricao = ' ${'a' * (tamanhoMinimoDescricao - 1)} ';
      expect(dadosValidos(descricao: descricao).validar(agora), {ErroOcorrencia.descricaoCurta});
    });
  });

  group('envolvido', () {
    test('nome não pode ter números', () {
      expect(validarNomeEnvolvido('Maria 2'), ErroEnvolvido.nomeComNumeros);
      expect(validarNomeEnvolvido('  '), ErroEnvolvido.nomeVazio);
      expect(validarNomeEnvolvido('Maria'), isNull);
    });

    test('documento opcional com 11 (CPF) ou 10 (RG) dígitos, máscara tolerada', () {
      expect(validarDocumento(null), isNull);
      expect(validarDocumento('123.456.789-01'), isNull);
      expect(validarDocumento('1234567890'), isNull);
      expect(validarDocumento('12345'), ErroEnvolvido.documentoInvalido);
      expect(validarDocumento('12345678ABC'), ErroEnvolvido.documentoInvalido);
    });
  });

  group('evidências', () {
    test('formato vem da extensão, sem diferenciar maiúsculas', () {
      expect(foto(nome: 'IMG.JPEG').formato, FormatoEvidencia.jpeg);
      expect(foto(nome: 'laudo.pdf').formato, FormatoEvidencia.pdf);
      expect(foto(nome: 'foto.heic').validar(), ErroEvidencia.formatoNaoSuportado);
    });

    test('recusa arquivo vazio e acima de 10 MB', () {
      expect(foto(tamanho: 0).validar(), ErroEvidencia.arquivoVazio);
      expect(
        foto(tamanho: tamanhoMaximoEvidenciaBytes + 1).validar(),
        ErroEvidencia.tamanhoExcedido,
      );
    });

    test('lote respeita o limite somando as já anexadas', () {
      final lote = [foto(), foto()];
      expect(validarLoteEvidencias(lote, jaAnexadas: maximoEvidenciasPorOcorrencia - 2), isNull);
      expect(
        validarLoteEvidencias(lote, jaAnexadas: maximoEvidenciasPorOcorrencia - 1),
        ErroEvidencia.limiteAtingido,
      );
    });
  });

  group('formato da evidência vindo do backend', () {
    test('aceita os códigos de EvidenciaSchema.formato', () {
      expect(FormatoEvidencia.doCodigo('jpg'), FormatoEvidencia.jpeg);
      expect(FormatoEvidencia.doCodigo('JPEG'), FormatoEvidencia.jpeg);
      expect(FormatoEvidencia.doCodigo('png'), FormatoEvidencia.png);
      expect(FormatoEvidencia.doCodigo('gif'), isNull);
    });

    test('só fotos são exibidas no app', () {
      Evidencia de(String formato) => Evidencia(
        id: 'ev',
        nomeOriginal: 'arquivo',
        formato: formato,
        tamanhoBytes: 1,
        hashSha256: 'a',
        enviadaEm: agora,
      );
      expect(de('jpg').ehImagem, isTrue);
      expect(de('png').ehImagem, isTrue);
      expect(de('pdf').ehImagem, isFalse);
      expect(de('desconhecido').ehImagem, isFalse);
    });
  });

  group('StatusOcorrencia', () {
    test('correção só em EM_CORRECAO e evidência só antes da decisão', () {
      expect(StatusOcorrencia.emCorrecao.aceitaCorrecao, isTrue);
      expect(StatusOcorrencia.aguardandoRevisao.aceitaCorrecao, isFalse);
      expect(StatusOcorrencia.aguardandoRevisao.aceitaEvidencia, isTrue);
      expect(StatusOcorrencia.validada.aceitaEvidencia, isFalse);
    });

    test('todos os códigos do backend são reconhecidos', () {
      const codigos = [
        'AGUARDANDO_REVISAO',
        'EM_CORRECAO',
        'REJEITADA',
        'VALIDADA',
        'EM_ATENDIMENTO',
        'ENCERRADA',
        'ARQUIVADA',
        'EXCLUIDA',
      ];
      expect(codigos.map(StatusOcorrencia.deCodigo).toSet(), StatusOcorrencia.values.toSet());
    });
  });

  test('FiltroOcorrencias tem igualdade por valor (chave de cache)', () {
    const a = FiltroOcorrencias(status: {StatusOcorrencia.emCorrecao, StatusOcorrencia.validada});
    const b = FiltroOcorrencias(status: {StatusOcorrencia.validada, StatusOcorrencia.emCorrecao});
    expect(a, b);
    expect(a.hashCode, b.hashCode);
    expect(a == const FiltroOcorrencias(somenteMinhas: true), isFalse);
  });
}
