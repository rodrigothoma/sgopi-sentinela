import '../../../core/http/json.dart';
import '../domain/notificacao.dart';

/// `NotificacaoSchema` e `ListaNotificacoesResponse` de `notificacoes_router.py`.
abstract final class NotificacaoMapper {
  static LoteNotificacoes loteDeJson(Json json) => LoteNotificacoes(
    itens: lista(json, 'itens').map(deJson).toList(),
    naoLidas: campo<int>(json, 'nao_lidas'),
  );

  static Notificacao deJson(Json json) => Notificacao(
    id: campo<String>(json, 'id'),
    titulo: campo<String>(json, 'titulo'),
    mensagem: campo<String>(json, 'mensagem'),
    tipo: campo<String>(json, 'tipo'),
    prioridade: campo<String>(json, 'prioridade'),
    lida: campo<bool>(json, 'lida'),
    criadaEm: data(json, 'criada_em'),
    link: campoOpcional<String>(json, 'link'),
  );
}
