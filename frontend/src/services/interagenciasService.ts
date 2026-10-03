import { api } from './api';

export interface Departamento {
  codigo: string;
  nome: string;
  descricao: string;
}

export interface ComunicacaoInteragencias {
  id: string;
  numero_oficio: string;
  departamento_origem: string;
  departamentos_destinatarios: string[];
  remetente_id: string;
  assunto: string;
  corpo: string;
  protocolo_ocorrencia?: string | null;
  nivel_sigilo: 'PUBLICO' | 'RESTRITO' | 'CONFIDENCIAL';
  prioridade: 'BAIXA' | 'MEDIA' | 'ALTA' | 'URGENTE';
  status_entrega: 'ENVIADO' | 'ENTREGUE' | 'LIDO' | 'RESPONDIDO' | 'ARQUIVADO';
  mensagem_pai_id?: string | null;
  criada_em: string;
}

export interface EnviarComunicacaoPayload {
  departamento_origem: string;
  departamentos_destinatarios: string[];
  assunto: string;
  corpo: string;
  prioridade: string;
  nivel_sigilo: string;
  protocolo_ocorrencia?: string | null;
}

export interface ResponderComunicacaoPayload {
  departamento_origem: string;
  assunto: string;
  corpo: string;
  prioridade: string;
}

export const interagenciasService = {
  async listarDepartamentos(): Promise<Departamento[]> {
    const res = await api.get<Departamento[]>('/v1/interagencias/departamentos');
    return res.data;
  },

  async listar(params?: {
    departamento?: string;
    protocolo?: string;
  }): Promise<ComunicacaoInteragencias[]> {
    const res = await api.get<ComunicacaoInteragencias[]>('/v1/interagencias', { params });
    return res.data;
  },

  async enviar(payload: EnviarComunicacaoPayload): Promise<ComunicacaoInteragencias> {
    const res = await api.post<ComunicacaoInteragencias>('/v1/interagencias', payload);
    return res.data;
  },

  async responder(id: string, payload: ResponderComunicacaoPayload): Promise<ComunicacaoInteragencias> {
    const res = await api.post<ComunicacaoInteragencias>(`/v1/interagencias/${id}/responder`, payload);
    return res.data;
  },
};
