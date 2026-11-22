import 'package:flutter_test/flutter_test.dart';
import 'package:sgopi_mobile/core/dominio/falha.dart';
import 'package:sgopi_mobile/features/ocorrencias/application/dependencias.dart';
import 'package:sgopi_mobile/features/ocorrencias/application/detalhe_ocorrencia.dart';
import 'package:sgopi_mobile/features/ocorrencias/application/lista_ocorrencias.dart';
import 'package:sgopi_mobile/features/ocorrencias/data/ocorrencia_mapper.dart';
import 'package:sgopi_mobile/features/ocorrencias/domain/arquivo_evidencia.dart';
import 'package:sgopi_mobile/features/ocorrencias/domain/dados_ocorrencia.dart';
import 'package:sgopi_mobile/features/ocorrencias/domain/ocorrencia.dart';

import '../../fakes/container.dart';
import '../../fakes/exemplos.dart';

void main() {
  late Dubles d;

  setUp(() => d = Dubles());

  group('RegistrarOcorrencia', () {
    test('dados inválidos não chegam ao backend', () async {
      final caso = d.container().read(registrarOcorrenciaProvider);
      await expectLater(
        caso.executar(dadosValidos(envolvidos: const []), const []),
        throwsA(isA<DadosOcorrenciaInvalidos>()),
      );
      expect(d.ocorrencias.registradas, isEmpty);
    });

    test('foto em formato não suportado é recusada antes do registro', () async {
      final caso = d.container().read(registrarOcorrenciaProvider);
      await expectLater(
        caso.executar(dadosValidos(), [foto(nome: 'foto.heic')]),
        throwsA(isA<EvidenciaInvalida>()),
      );
      expect(d.ocorrencias.registradas, isEmpty);
    });

    test('registra e envia as fotos; uma recusada não desfaz o protocolo', () async {
      d.ocorrencias.anexosRecusados.add('ruim.jpg');
      final caso = d.container().read(registrarOcorrenciaProvider);
      final resultado = await caso.executar(dadosValidos(), [
        foto(nome: 'boa.jpg'),
        foto(nome: 'ruim.jpg'),
      ]);

      expect(resultado.protocolo.numeroProtocolo, 'BO-2026-000999');
      expect(d.ocorrencias.anexos.single.$2.nome, 'boa.jpg');
      expect(resultado.evidenciasNaoEnviadas.single.arquivo.nome, 'ruim.jpg');
      expect(resultado.evidenciasNaoEnviadas.single.erro, isA<Falha>());
    });
  });

  group('CorrigirOcorrencia', () {
    final atual = OcorrenciaMapper.detalheDeJson(
      detalheJson(status: 'EM_CORRECAO', evidencias: maximoEvidenciasPorOcorrencia - 1),
    );

    setUp(() => d.ocorrencias.ocorrencias[atual.id] = atual);

    test('envia a correção e as novas fotos', () async {
      final caso = d.container().read(corrigirOcorrenciaProvider);
      final resultado = await caso.executar(atual, dadosValidos(), [foto()]);
      expect(d.ocorrencias.correcoes.single.$1, atual.id);
      expect(d.ocorrencias.anexos, hasLength(1));
      expect(resultado.evidenciasNaoEnviadas, isEmpty);
    });

    test('conta as evidências já anexadas no limite', () async {
      final caso = d.container().read(corrigirOcorrenciaProvider);
      await expectLater(
        caso.executar(atual, dadosValidos(), [foto(), foto()]),
        throwsA(
          isA<EvidenciaInvalida>().having((e) => e.erro, 'erro', ErroEvidencia.limiteAtingido),
        ),
      );
      expect(d.ocorrencias.correcoes, isEmpty);
    });
  });

  group('ListaOcorrencias', () {
    const filtro = FiltroOcorrencias(somenteMinhas: true);

    setUp(() {
      for (var i = 0; i < tamanhoPaginaOcorrencias + 5; i++) {
        final o = OcorrenciaMapper.detalheDeJson(detalheJson(id: 'oc-$i'));
        d.ocorrencias.ocorrencias[o.id] = o;
      }
    });

    test('carrega a primeira página e depois a seguinte', () async {
      final container = d.container();
      final provider = listaOcorrenciasProvider(filtro);
      container.listen(provider, (_, _) {});

      final primeira = await container.read(provider.future);
      expect(primeira.itens, hasLength(tamanhoPaginaOcorrencias));
      expect(primeira.temMais, isTrue);

      await container.read(provider.notifier).carregarMais();
      final tudo = container.read(provider).value!;
      expect(tudo.itens, hasLength(tamanhoPaginaOcorrencias + 5));
      expect(tudo.temMais, isFalse);
      expect(d.ocorrencias.consultas.last.$3, tamanhoPaginaOcorrencias);
    });

    test('falha ao carregar mais mantém os itens e registra o erro', () async {
      final container = d.container();
      final provider = listaOcorrenciasProvider(filtro);
      container.listen(provider, (_, _) {});
      await container.read(provider.future);

      d.ocorrencias.falhaNaListagem = const Falha(TipoFalha.semConexao);
      await container.read(provider.notifier).carregarMais();
      final estado = container.read(provider).value!;
      expect(estado.itens, hasLength(tamanhoPaginaOcorrencias));
      expect(estado.erroAoCarregarMais, isA<Falha>());
    });
  });

  group('DetalheOcorrencia', () {
    test('anexar acima do limite é recusado sem chamar o backend', () async {
      final cheia = OcorrenciaMapper.detalheDeJson(
        detalheJson(evidencias: maximoEvidenciasPorOcorrencia),
      );
      d.ocorrencias.ocorrencias[cheia.id] = cheia;
      final container = d.container();
      final provider = detalheOcorrenciaProvider(cheia.id);
      container.listen(provider, (_, _) {});
      await container.read(provider.future);

      await expectLater(
        container.read(provider.notifier).anexar(foto()),
        throwsA(isA<EvidenciaInvalida>()),
      );
      expect(d.ocorrencias.anexos, isEmpty);
    });

    test('reenviar atualiza o estado com a resposta do backend', () async {
      final emCorrecao = OcorrenciaMapper.detalheDeJson(detalheJson(status: 'EM_CORRECAO'));
      d.ocorrencias.ocorrencias[emCorrecao.id] = emCorrecao;
      final container = d.container();
      final provider = detalheOcorrenciaProvider(emCorrecao.id);
      container.listen(provider, (_, _) {});
      await container.read(provider.future);

      await container.read(provider.notifier).reenviar();
      expect(container.read(provider).value!.status.aguardaRevisao, isTrue);
    });
  });
}
