import { api } from './api';

export type TipoNotificacao =
  | 'ALERTA_CRITICIDADE'
  | 'ALERTA_VENCIMENTO_MEDIDA'
  | 'COMUNICACAO_INTERAGENCIAS'
  | 'REVISAO_OCORRENCIA'
  | 'SISTEMA';

export type PrioridadeNotificacao = 'BAIXA' | 'MEDIA' | 'ALTA' | 'URGENTE';

export interface Notificacao {
  id: string;
  usuario_id: string;
  titulo: string;
  mensagem: string;
  tipo: TipoNotificacao;
  prioridade: PrioridadeNotificacao;
  lida: boolean;
  lida_em?: string | null;
  criada_em: string;
  /** Rota interna para onde o clique leva (ex.: ``/minhas?ocorrencia=...``). */
  link?: string | null;
}

export interface ResumoNotificacoes {
  total: number;
  nao_lidas: number;
}

export interface PaginaNotificacoes {
  itens: Notificacao[];
  total: number;
  nao_lidas: number;
  offset: number;
  limite: number;
}

export const notificacoesService = {
  async listar(params?: {
    limite?: number;
    offset?: number;
    apenas_nao_lidas?: boolean;
  }): Promise<PaginaNotificacoes> {
    const res = await api.get<PaginaNotificacoes>('/v1/notificacoes', { params });
    return res.data;
  },

  async obterResumo(): Promise<ResumoNotificacoes> {
    const res = await api.get<ResumoNotificacoes>('/v1/notificacoes/resumo');
    return res.data;
  },

  async marcarComoLida(id: string): Promise<Notificacao> {
    const res = await api.patch<Notificacao>(`/v1/notificacoes/${id}/lida`);
    return res.data;
  },

  async marcarTodasComoLidas(): Promise<{ atualizadas: number }> {
    const res = await api.post<{ atualizadas: number }>('/v1/notificacoes/marcar-todas-lidas');
    return res.data;
  },
};
