import { api } from './api';
import type { AutoApreensao, ItemApreendido, ItemApreendidoDTO, MovimentarCustodiaRequest } from '../types/api';

/** RF03 / UC03 — inventário de apreensões e cadeia de custódia de uma ocorrência. */
export const apreensoesService = {
  /** Somente AGENTE autor; lacre único em toda a base. */
  async registrar(ocorrenciaId: string, item: ItemApreendidoDTO): Promise<ItemApreendido> {
    return (await api.post<ItemApreendido>(`/v1/ocorrencias/${ocorrenciaId}/apreensoes`, item)).data;
  },
  /** AGENTE autor ou DELEGADO; evento append-only (quem, quando, de onde, para onde). */
  async movimentar(ocorrenciaId: string, itemId: string, data: MovimentarCustodiaRequest): Promise<ItemApreendido> {
    return (await api.post<ItemApreendido>(`/v1/ocorrencias/${ocorrenciaId}/apreensoes/${itemId}/movimentacoes`, data)).data;
  },
  /** Emissão auditada: identificador único + hash SHA-256 do conteúdo. */
  async emitirAuto(ocorrenciaId: string): Promise<AutoApreensao> {
    return (await api.get<AutoApreensao>(`/v1/ocorrencias/${ocorrenciaId}/auto-apreensao`)).data;
  },
};
