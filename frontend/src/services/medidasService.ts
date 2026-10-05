import { api } from './api';

export interface MedidaProtetiva {
  id: string;
  numero_referencia: string;
  ocorrencia_id: string;
  delegado_id: string;
  vitima_id: string;
  agressor_id: string;
  tipos_restricao: string[];
  distancia_minima_metros?: number | null;
  data_inicio: string;
  prazo_dias: number;
  data_vencimento: string;
  dias_restantes: number;
  status: string;
  condicoes_especificas?: string | null;
  motivo_revogacao?: string | null;
  justificativa_renovacao?: string | null;
  alerta_vencimento_enviado?: boolean;
  criada_em: string;
}

export interface ResultadoVerificacaoVencimentos {
  processadas: number;
  alertas_enviados: number;
  itens: Array<{
    id: string;
    numero_referencia: string;
    dias_restantes: number;
    email_destinatario: string;
    enviado: boolean;
  }>;
}

export interface ResultadoAlertaManual {
  medida_id: string;
  email_destinatario: string;
  enviado: boolean;
  dias_restantes: number;
  mensagem: string;
}

export interface PaginaMedidas {
  itens: MedidaProtetiva[];
  total: number;
  offset: number;
  limit: number;
}

export const medidasService = {
  async listar(params?: {
    status?: string[];
    ocorrencia_id?: string;
    limit?: number;
    offset?: number;
  }): Promise<PaginaMedidas> {
    const res = await api.get<PaginaMedidas>('/v1/medidas-protetivas', { params });
    return res.data;
  },

  async conceder(dados: {
    ocorrencia_id: string;
    vitima_id: string;
    agressor_id: string;
    tipos_restricao: string[];
    prazo_dias: number;
    data_inicio?: string;
    distancia_minima_metros?: number;
    condicoes_especificas?: string;
  }): Promise<MedidaProtetiva> {
    const res = await api.post<MedidaProtetiva>('/v1/medidas-protetivas', dados);
    return res.data;
  },

  async renovar(id: string, dados: { dias_adicionais: number; justificativa: string }): Promise<MedidaProtetiva> {
    const res = await api.post<MedidaProtetiva>(`/v1/medidas-protetivas/${id}/renovar`, dados);
    return res.data;
  },

  async revogar(id: string, dados: { motivo: string }): Promise<MedidaProtetiva> {
    const res = await api.post<MedidaProtetiva>(`/v1/medidas-protetivas/${id}/revogar`, dados);
    return res.data;
  },

  async verificarVencimentos(): Promise<ResultadoVerificacaoVencimentos> {
    const res = await api.post<ResultadoVerificacaoVencimentos>('/v1/medidas-protetivas/verificar-vencimentos');
    return res.data;
  },

  async enviarAlertaVencimento(id: string, email_destinatario?: string): Promise<ResultadoAlertaManual> {
    const res = await api.post<ResultadoAlertaManual>(`/v1/medidas-protetivas/${id}/enviar-alerta-vencimento`, {
      email_destinatario: email_destinatario || null,
    });
    return res.data;
  },
};
