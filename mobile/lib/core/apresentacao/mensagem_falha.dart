import '../dominio/falha.dart';
import '../l10n/gerado/textos.dart';

/// Texto exibido para uma [Falha], no mesmo padrão do frontend web:
/// a mensagem traduzida pelo backend seguida de `(ref. <request_id curto>)`.
String mensagemDeFalha(Textos textos, Falha falha) {
  final aguardar = falha.aguardarPor;
  final base = switch (falha.tipo) {
    TipoFalha.semConexao => textos.erroSemConexao,
    TipoFalha.muitasTentativas when aguardar != null => textos.loginBloqueado(
      (aguardar.inSeconds / Duration.secondsPerMinute).ceil(),
    ),
    TipoFalha.acessoNegado when falha.detalhe == null => textos.erroAcessoNegado,
    _ => falha.detalhe ?? textos.erroInesperado,
  };
  final referencia = falha.referencia;
  return referencia == null ? base : '$base ${textos.referenciaErro(referencia)}';
}
