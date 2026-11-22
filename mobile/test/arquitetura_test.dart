// Fitness functions da arquitetura hexagonal do app, no papel do import-linter do
// backend (`backend/pyproject.toml`) e de `backend/tests/unit/test_architecture_solid.py`.
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

final _raiz = Directory('lib').absolute.path;
final _importacao = RegExp(r'''^\s*(?:import|export)\s+['"]([^'"]+)['"]''', multiLine: true);

/// Arquivo de `lib/` com os destinos dos seus imports normalizados:
/// `package:x/...` vira `pkg:x`; caminhos do próprio app viram `lib/...`.
final class _Fonte {
  _Fonte(this.caminho, this.destinos);

  final String caminho;
  final List<String> destinos;

  bool em(String prefixo) => caminho.startsWith(prefixo);
}

List<_Fonte> _fontes() =>
    Directory('lib')
        .listSync(recursive: true)
        .whereType<File>()
        .where((f) => f.path.endsWith('.dart') && !f.path.contains('/gerado/'))
        .map((f) => _Fonte(_relativo(f.absolute.path), _destinos(f)))
        .toList();

List<String> _destinos(File arquivo) => [
  for (final m in _importacao.allMatches(arquivo.readAsStringSync()))
    _normalizar(arquivo, m.group(1)!),
];

String _normalizar(File origem, String alvo) {
  if (alvo.startsWith('dart:')) return alvo;
  if (alvo.startsWith('package:sgopi_mobile/')) return 'lib/${alvo.substring(21)}';
  if (alvo.startsWith('package:')) return 'pkg:${alvo.substring(8).split('/').first}';
  return _relativo(Uri.file(origem.absolute.path).resolve(alvo).toFilePath());
}

String _relativo(String absoluto) => 'lib${absoluto.substring(_raiz.length)}';

bool _camada(String destino, String camada) =>
    RegExp('^lib/features/[^/]+/$camada/').hasMatch(destino);

bool _dominio(String d) => _camada(d, 'domain') || d.startsWith('lib/core/dominio/');

/// Bibliotecas do SDK sem E/S nem Flutter (`dart:async`, `dart:typed_data`...).
bool _dartPuro(String d) => d.startsWith('dart:') && d != 'dart:io' && d != 'dart:ui';

bool _aplicacao(String d) => _camada(d, 'application') || d.startsWith('lib/core/aplicacao/');

void _semViolacoes(Iterable<_Fonte> fontes, bool Function(String destino) proibido) {
  final violacoes = [
    for (final f in fontes)
      for (final d in f.destinos.where(proibido)) '${f.caminho} -> $d',
  ];
  expect(violacoes, isEmpty, reason: violacoes.join('\n'));
}

void main() {
  final fontes = _fontes();

  test('domain é Dart puro: só dart:* e outros domínios', () {
    _semViolacoes(fontes.where((f) => _dominio(f.caminho)), (d) => !_dartPuro(d) && !_dominio(d));
  });

  test('application só enxerga Dart puro, domain, application e o riverpod puro', () {
    _semViolacoes(
      fontes.where((f) => _aplicacao(f.caminho)),
      (d) => !_dartPuro(d) && d != 'pkg:riverpod' && !_dominio(d) && !_aplicacao(d),
    );
  });

  test('presentation não conhece adaptadores nem bibliotecas de infraestrutura', () {
    const infraestrutura = {
      'pkg:dio',
      'pkg:geolocator',
      'pkg:image_picker',
      'pkg:flutter_secure_storage',
      'pkg:shared_preferences',
      'pkg:package_info_plus',
    };
    _semViolacoes(
      fontes.where((f) => _camada(f.caminho, 'presentation') || f.em('lib/core/apresentacao/')),
      (d) =>
          _camada(d, 'data') ||
          d.startsWith('lib/core/http/') ||
          d.startsWith('lib/app/') ||
          infraestrutura.contains(d),
    );
  });

  test('data não depende de presentation nem de app', () {
    _semViolacoes(
      fontes.where((f) => _camada(f.caminho, 'data') || f.em('lib/core/http/')),
      (d) =>
          _camada(d, 'presentation') || d.startsWith('lib/app/') || d.startsWith('pkg:material_ui'),
    );
  });

  test('só o composition root (app/di.dart) instancia adaptadores de data/', () {
    _semViolacoes(
      fontes.where((f) => !_camada(f.caminho, 'data') && f.caminho != 'lib/app/di.dart'),
      (d) => _camada(d, 'data'),
    );
  });

  test('core não depende de features', () {
    _semViolacoes(fontes.where((f) => f.em('lib/core/')), (d) => d.startsWith('lib/features/'));
  });
}
