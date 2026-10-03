import { api } from './api';

export interface AreaRisco {
  id: string;
  nome: string;
  latitude: number;
  longitude: number;
  raio_metros: number;
  nivel_risco: 'BAIXA' | 'MEDIA' | 'ALTA' | 'CRITICA';
  total_ocorrencias: number;
  total_24h: number;
  naturezas_predominantes: string[];
  protocolos: string[];
}

export interface EmitirAlertaPayload {
  titulo: string;
  mensagem: string;
  area_risco_id?: string;
  latitude?: number;
  longitude?: number;
  raio_metros?: number;
  nivel_criticidade?: 'MEDIA' | 'ALTA' | 'CRITICA';
  papel_destinatario?: string | null;
}

export interface AlertaCriticidadeResponse {
  alerta_id: string;
  titulo: string;
  status: string;
  criada_em: string;
}

export interface ConfirmarCienciaResponse {
  sucesso: boolean;
  alerta_id: string;
  status: string;
}

export const inteligenciaService = {
  async obterAreasRisco(dias: number = 7): Promise<AreaRisco[]> {
    const res = await api.get<AreaRisco[]>('/v1/inteligencia/areas-risco', {
      params: { dias },
    });
    return res.data;
  },

  async emitirAlertaCriticidade(payload: EmitirAlertaPayload): Promise<AlertaCriticidadeResponse> {
    const res = await api.post<AlertaCriticidadeResponse>('/v1/inteligencia/alertas-criticidade/emitir', payload);
    return res.data;
  },

  async confirmarCienciaAlerta(alertaId: string): Promise<ConfirmarCienciaResponse> {
    const res = await api.post<ConfirmarCienciaResponse>(`/v1/inteligencia/alertas-criticidade/${alertaId}/confirmar-ciencia`);
    return res.data;
  },
};
