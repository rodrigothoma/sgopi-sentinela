/// Aviso do backend ao usuário (`/v1/notificacoes`). Título e mensagem chegam
/// prontos do servidor, que hoje os grava só em português.
final class Notificacao {
  const Notificacao({
    required this.id,
    required this.titulo,
    required this.mensagem,
    required this.tipo,
    required this.prioridade,
    required this.lida,
    required this.criadaEm,
    this.link,
  });

  final String id;
  final String titulo;
  final String mensagem;

  /// `TipoNotificacao` do backend (ex.: `REVISAO_OCORRENCIA`, `NOVA_OCORRENCIA`).
  final String tipo;

  /// `PrioridadeNotificacao` do backend: `BAIXA`, `MEDIA`, `ALTA` ou `CRITICA`.
  final String prioridade;
  final bool lida;
  final DateTime criadaEm;

  /// Rota do frontend web, ex.: `/minhas?protocolo=...&ocorrencia=<id>`.
  final String? link;

  bool get importante => prioridade == 'ALTA' || prioridade == 'CRITICA';

  /// Ocorrência citada no link, para abrir direto no app.
  String? get ocorrenciaVinculada {
    final destino = link;
    if (destino == null) return null;
    final id = Uri.tryParse(destino)?.queryParameters['ocorrencia'];
    return (id == null || id.isEmpty) ? null : id;
  }

  Notificacao marcadaComoLida() => Notificacao(
    id: id,
    titulo: titulo,
    mensagem: mensagem,
    tipo: tipo,
    prioridade: prioridade,
    lida: true,
    criadaEm: criadaEm,
    link: link,
  );
}

/// Uma página de notificações com o total de não lidas do usuário.
final class LoteNotificacoes {
  const LoteNotificacoes({required this.itens, required this.naoLidas});

  final List<Notificacao> itens;
  final int naoLidas;
}
