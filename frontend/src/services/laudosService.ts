import { api, API_BASE_URL } from './api';

export interface Laudo {
  id: string;
  numero_referencia: string;
  tipo_pericia: string;
  descricao_solicitacao: string;
  solicitante_id: string;
  status: string;
  solicitado_em: string;
  atualizado_em: string;
  perito_id?: string | null;
  ocorrencia_id?: string | null;
  inquerito_id?: string | null;
  item_apreendido_id?: string | null;
  conclusoes_tecnicas?: string | null;
  arquivo_nome?: string | null;
  hash_sha256?: string | null;
  concluido_em?: string | null;
}

export interface PaginaLaudos {
  itens: Laudo[];
  total: number;
  offset: number;
  limit: number;
}

export const laudosService = {
  async listar(params?: {
    status?: string[];
    ocorrencia_id?: string;
    inquerito_id?: string;
    limit?: number;
    offset?: number;
  }): Promise<PaginaLaudos> {
    const res = await api.get<PaginaLaudos>('/v1/laudos', { params });
    return res.data;
  },

  async obter(id: string): Promise<Laudo> {
    const res = await api.get<Laudo>(`/v1/laudos/${id}`);
    return res.data;
  },

  async solicitar(dados: {
    tipo_pericia: string;
    descricao_solicitacao: string;
    ocorrencia_id?: string;
    inquerito_id?: string;
    item_apreendido_id?: string;
  }): Promise<Laudo> {
    const res = await api.post<Laudo>('/v1/laudos', dados);
    return res.data;
  },

  async anexar(id: string, conclusoes_tecnicas: string, arquivo: File): Promise<Laudo> {
    const formData = new FormData();
    formData.append('conclusoes_tecnicas', conclusoes_tecnicas);
    formData.append('arquivo', arquivo);
    const res = await api.post<Laudo>(`/v1/laudos/${id}/anexar`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },

  downloadUrl(id: string): string {
    return `${API_BASE_URL}/v1/laudos/${id}/download`;
  },
};
