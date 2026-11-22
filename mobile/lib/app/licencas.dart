import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';

/// Licenças das fontes embutidas, listadas em Ajustes → Licenças.
void registrarLicencasDasFontes() {
  const fontes = {
    'Plus Jakarta Sans': 'assets/fontes/OFL-PlusJakartaSans.txt',
    'Rajdhani': 'assets/fontes/OFL-Rajdhani.txt',
    'JetBrains Mono': 'assets/fontes/OFL-JetBrainsMono.txt',
  };
  LicenseRegistry.addLicense(() async* {
    for (final MapEntry(key: nome, value: arquivo) in fontes.entries) {
      yield LicenseEntryWithLineBreaks([nome], await rootBundle.loadString(arquivo));
    }
  });
}
