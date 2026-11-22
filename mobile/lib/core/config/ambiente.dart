/// Configuração por ambiente, injetada na compilação:
/// `flutter run --dart-define=API_BASE_URL=http://192.168.0.10:8000`.
///
/// O padrão `10.0.2.2` é o endereço da máquina hospedeira visto do emulador Android.
abstract final class Ambiente {
  static const urlBaseApi = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000',
  );
}
