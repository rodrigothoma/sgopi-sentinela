/// Aparência escolhida pelo usuário; [sistema] acompanha o aparelho.
enum ModoTema { sistema, claro, escuro }

/// Idioma da interface e das mensagens do backend (`Accept-Language`).
enum IdiomaApp {
  sistema(null),
  pt('pt'),
  en('en');

  const IdiomaApp(this.codigo);

  /// `null` para [sistema].
  final String? codigo;

  static IdiomaApp doCodigo(String? codigo) =>
      values.firstWhere((i) => i.codigo == codigo, orElse: () => sistema);

  /// Idioma efetivo: o escolhido ou, em [sistema], o do aparelho. O backend
  /// traduz para `pt` e `en`; qualquer outro idioma cai em `pt`.
  String resolver(String idiomaDoAparelho) => codigo ?? (idiomaDoAparelho == 'en' ? 'en' : 'pt');
}

final class Preferencias {
  const Preferencias({this.tema = ModoTema.sistema, this.idioma = IdiomaApp.sistema});

  final ModoTema tema;
  final IdiomaApp idioma;

  Preferencias copyWith({ModoTema? tema, IdiomaApp? idioma}) =>
      Preferencias(tema: tema ?? this.tema, idioma: idioma ?? this.idioma);

  @override
  bool operator ==(Object other) =>
      other is Preferencias && other.tema == tema && other.idioma == idioma;

  @override
  int get hashCode => Object.hash(tema, idioma);
}
