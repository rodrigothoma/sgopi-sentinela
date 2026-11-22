import '../../../core/http/json.dart';
import '../domain/papel.dart';
import '../domain/sessao.dart';
import '../domain/usuario.dart';

/// Converte a resposta de `POST /v1/auth/login` e o formato salvo no aparelho.
abstract final class SessaoMapper {
  /// `{access_token, token_type, expira_em, usuario: {id, nome, login, papel}}`.
  static Sessao deJson(Json json) => Sessao(
    token: campo<String>(json, 'access_token'),
    expiraEm: data(json, 'expira_em'),
    usuario: _usuario(campo<Json>(json, 'usuario')),
  );

  /// Mesmo formato da resposta de login, para reaproveitar [deJson] ao restaurar.
  static Json paraJson(Sessao sessao) => {
    'access_token': sessao.token,
    'expira_em': dataParaApi(sessao.expiraEm),
    'usuario': {
      'id': sessao.usuario.id,
      'nome': sessao.usuario.nome,
      'login': sessao.usuario.login,
      'papel': sessao.usuario.papel.codigo,
    },
  };

  static Usuario _usuario(Json json) => Usuario(
    id: campo<String>(json, 'id'),
    nome: campo<String>(json, 'nome'),
    login: campo<String>(json, 'login'),
    papel: Papel.deCodigo(campo<String>(json, 'papel')),
  );
}
