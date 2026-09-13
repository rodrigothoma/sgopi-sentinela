import axios from 'axios';
import type { RegistrarOcorrenciaRequest, OcorrenciaResponse } from '../types/ocorrencia';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
});

export const ocorrenciasService = {
  async registrar(data: RegistrarOcorrenciaRequest): Promise<OcorrenciaResponse> {
    const response = await api.post<OcorrenciaResponse>('/v1/ocorrencias/', data);
    return response.data;
  },

  async buscarPorId(id: string): Promise<OcorrenciaResponse> {
    const response = await api.get<OcorrenciaResponse>(`/v1/ocorrencias/${id}`);
    return response.data;
  },
};
