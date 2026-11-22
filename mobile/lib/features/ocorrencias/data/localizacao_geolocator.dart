import 'package:geolocator/geolocator.dart';

import '../domain/ocorrencia.dart';
import '../domain/portas.dart';

const _tempoLimiteLeitura = Duration(seconds: 20);

/// GPS do aparelho via `geolocator`, pedindo permissão na primeira vez.
final class LocalizacaoGeolocator implements PortaLocalizacao {
  const LocalizacaoGeolocator();

  @override
  Future<Coordenada> obterAtual() async {
    if (!await Geolocator.isLocationServiceEnabled()) {
      throw const LocalizacaoIndisponivel(MotivoLocalizacaoIndisponivel.servicoDesligado);
    }
    await _garantirPermissao();
    try {
      final posicao = await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(
          accuracy: LocationAccuracy.high,
          timeLimit: _tempoLimiteLeitura,
        ),
      );
      return Coordenada(latitude: posicao.latitude, longitude: posicao.longitude);
    } on Exception {
      throw const LocalizacaoIndisponivel(MotivoLocalizacaoIndisponivel.falhaLeitura);
    }
  }

  Future<void> _garantirPermissao() async {
    var permissao = await Geolocator.checkPermission();
    if (permissao == LocationPermission.denied) {
      permissao = await Geolocator.requestPermission();
    }
    if (permissao == LocationPermission.denied || permissao == LocationPermission.deniedForever) {
      throw const LocalizacaoIndisponivel(MotivoLocalizacaoIndisponivel.permissaoNegada);
    }
  }
}
