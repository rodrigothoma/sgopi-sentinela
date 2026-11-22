import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

Set<String> _chaves(String idioma) {
  final arb = jsonDecode(File('lib/core/l10n/app_$idioma.arb').readAsStringSync()) as Map;
  return arb.keys.cast<String>().where((k) => !k.startsWith('@')).toSet();
}

void main() {
  test('pt e en têm exatamente as mesmas chaves', () {
    final pt = _chaves('pt');
    final en = _chaves('en');
    expect(pt.difference(en), isEmpty, reason: 'faltando em app_en.arb');
    expect(en.difference(pt), isEmpty, reason: 'faltando em app_pt.arb');
  });

  test('nenhum texto em inglês ficou vazio ou igual a uma chave', () {
    final arb = jsonDecode(File('lib/core/l10n/app_en.arb').readAsStringSync()) as Map;
    for (final MapEntry(:key, :value) in arb.entries) {
      if ((key as String).startsWith('@')) continue;
      expect((value as String).trim(), isNotEmpty, reason: key);
      expect(value, isNot(key), reason: key);
    }
  });
}
