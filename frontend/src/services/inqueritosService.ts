import { api } from './api';

export interface OcorrenciaResumoInquerito {
  id: string;
  numero_protocolo: string;
  natureza: string;
  localizacao: string;
  data_hora_fato: string;
  status: string;
}

export interface Inquerito {
  id: string;
  numero: string;
  ementa: string;
  delegado_id: string;
  status: string;
  data_abertura: string;
  atualizado_em: string;
  ocorrencias: OcorrenciaResumoInquerito[];
  relatorio_final?: string | null;
  motivo_arquivamento?: string | null;
  concluido_em?: string | null;
}

export interface PaginaInqueritos {
  itens: Inquerito[];
  total: number;
  offset: number;
  limit: number;
}

export interface ConexaoSugerida {
  ocorrencia_id: string;
  numero_protocolo: string;
  natureza: string;
  localizacao: string;
  score_similaridade: number;
  motivos: string[];
}

export const inqueritosService = {
  async listar(params?: { status?: string[]; limit?: number; offset?: number }): Promise<PaginaInqueritos> {
    const res = await api.get<PaginaInqueritos>('/v1/inqueritos', { params });
    return res.data;
  },

  async obter(id: string): Promise<Inquerito> {
    const res = await api.get<Inquerito>(`/v1/inqueritos/${id}`);
    return res.data;
  },

  async instaurar(dados: { ementa: string; ocorrencias_iniciais_ids?: string[] }): Promise<Inquerito> {
    const res = await api.post<Inquerito>('/v1/inqueritos', dados);
    return res.data;
  },

  async vincularOcorrencias(id: string, ocorrencias_ids: string[]): Promise<Inquerito> {
    const res = await api.post<Inquerito>(`/v1/inqueritos/${id}/ocorrencias`, { ocorrencias_ids });
    return res.data;
  },

  async concluir(id: string, relatorio_final: string): Promise<Inquerito> {
    const res = await api.post<Inquerito>(`/v1/inqueritos/${id}/concluir`, { relatorio_final });
    return res.data;
  },

  async buscarConexoes(ocorrencia_id: string): Promise<ConexaoSugerida[]> {
    const res = await api.get<ConexaoSugerida[]>(`/v1/inqueritos/conexoes/${ocorrencia_id}`);
    return res.data;
  },
};
