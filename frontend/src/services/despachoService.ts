import { api } from './api';
import type { OrdemDespacho, Sugestoes } from '../types/api';

export const despachoService = {
  async sugestoes(ocorrenciaId: string): Promise<Sugestoes> {
    return (await api.get<Sugestoes>(`/v1/ocorrencias/${ocorrenciaId}/sugestoes-viaturas`)).data;
  },
  async despachar(ocorrenciaId: string, viaturaId: string, observacoes?: string): Promise<OrdemDespacho> {
    return (await api.post<OrdemDespacho>('/v1/despachos', { ocorrencia_id: ocorrenciaId, viatura_id: viaturaId, observacoes })).data;
  },
  async listar(somenteAtivas = true): Promise<OrdemDespacho[]> {
    return (await api.get<OrdemDespacho[]>('/v1/despachos', { params: { somente_ativas: somenteAtivas } })).data;
  },
};
