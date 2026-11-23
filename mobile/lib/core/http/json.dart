/// Leitura tipada de JSON vindo do backend. Campo ausente ou com tipo errado é
/// quebra de contrato e falha com [FormatException] apontando o campo.
typedef Json = Map<String, dynamic>;

T campo<T>(Json json, String nome) {
  final valor = json[nome];
  if (valor is T) return valor;
  throw FormatException('Campo "$nome" ausente ou inválido: $valor');
}

T? campoOpcional<T>(Json json, String nome) {
  final valor = json[nome];
  return valor is T ? valor : null;
}

DateTime data(Json json, String nome) => DateTime.parse(campo<String>(json, nome));

double numero(Json json, String nome) => campo<num>(json, nome).toDouble();

List<Json> lista(Json json, String nome) => (json[nome] as List<dynamic>? ?? const []).cast<Json>();

/// Datas vão ao backend sempre em UTC com fuso explícito (o backend recusa datas sem fuso).
String dataParaApi(DateTime instante) => instante.toUtc().toIso8601String();
