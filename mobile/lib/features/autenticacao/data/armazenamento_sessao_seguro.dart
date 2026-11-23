import 'dart:convert';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../../../core/http/json.dart';
import '../domain/portas.dart';
import '../domain/sessao.dart';
import 'sessao_mapper.dart';

/// Guarda o token no Keystore do Android (via `flutter_secure_storage`), nunca em texto puro.
final class ArmazenamentoSessaoSeguro implements ArmazenamentoSessao {
  ArmazenamentoSessaoSeguro(this._armazenamento);

  static const _chave = 'sgopi.sessao';

  final FlutterSecureStorage _armazenamento;

  /// Conteúdo ilegível (versão antiga, dado corrompido) é descartado como "sem sessão".
  @override
  Future<Sessao?> carregar() async {
    final conteudo = await _armazenamento.read(key: _chave);
    if (conteudo == null) return null;
    try {
      return SessaoMapper.deJson(jsonDecode(conteudo) as Json);
    } on Object {
      await limpar();
      return null;
    }
  }

  @override
  Future<void> salvar(Sessao sessao) =>
      _armazenamento.write(key: _chave, value: jsonEncode(SessaoMapper.paraJson(sessao)));

  @override
  Future<void> limpar() => _armazenamento.delete(key: _chave);
}
