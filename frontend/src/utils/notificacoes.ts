import type { Notificacao, PrioridadeNotificacao, TipoNotificacao } from '../services/notificacoesService';

export const LIMITE_NOTIFICACOES = 15;

/** Mantém a conversão usada pelo sino para eventos recebidos antes da próxima consulta REST. */
export function notificacaoDoEvento(d: Record<string, unknown>): Notificacao {
  return {
    id: String(d.id ?? ''),
    usuario_id: (d.usuario_id as string) ?? '',
    titulo: String(d.titulo ?? ''),
    mensagem: String(d.mensagem ?? ''),
    tipo: (d.tipo as TipoNotificacao) ?? 'SISTEMA',
    prioridade: (d.prioridade as PrioridadeNotificacao) ?? 'MEDIA',
    lida: false,
    criada_em: String(d.criada_em ?? new Date().toISOString()),
    link: (d.link as string) ?? null,
  };
}

/** Eventos mais recentes aparecem primeiro, respeitando o limite visual do sino. */
export function inserirNotificacao(itens: Notificacao[], nova: Notificacao): Notificacao[] {
  return [nova, ...itens].slice(0, LIMITE_NOTIFICACOES);
}
