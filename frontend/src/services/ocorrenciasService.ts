import { api } from './api';
import type {
  CorrigirOcorrenciaRequest, Evidencia, IntegridadeEvidencia, OcorrenciaCriada, OcorrenciaDetalhe, OcorrenciaResumo, Pagina,
  RegistrarOcorrenciaRequest, StatusOcorrencia,
} from '../types/api';

export const ocorrenciasService = {
  async registrar(data: RegistrarOcorrenciaRequest): Promise<OcorrenciaCriada> {
    return (await api.post<OcorrenciaCriada>('/v1/ocorrencias', data)).data;
  },
  async anexarEvidencia(id: string, arquivo: File): Promise<Evidencia> {
    const body = new FormData();
    body.append('arquivo', arquivo);
    return (await api.post<Evidencia>(`/v1/ocorrencias/${id}/evidencias`, body)).data;
  },
  async verificarIntegridade(ocorrenciaId: string, evidenciaId: string): Promise<IntegridadeEvidencia> {
    return (await api.get<IntegridadeEvidencia>(`/v1/ocorrencias/${ocorrenciaId}/evidencias/${evidenciaId}/integridade`)).data;
  },
  async baixarEvidencia(ocorrenciaId: string, evidencia: Evidencia): Promise<void> {
    const resposta = await api.get<Blob>(`/v1/ocorrencias/${ocorrenciaId}/evidencias/${evidencia.id}/download`, { responseType: 'blob' });
    const url = URL.createObjectURL(resposta.data);
    const link = document.createElement('a');
    link.href = url;
    link.download = evidencia.nome_original;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  },
  async listar(status: StatusOcorrencia[] = [], limit = 50, offset = 0): Promise<Pagina<OcorrenciaResumo>> {
    const params = new URLSearchParams();
    status.forEach((s) => params.append('status', s));
    params.set('limit', String(limit));
    params.set('offset', String(offset));
    return (await api.get<Pagina<OcorrenciaResumo>>('/v1/ocorrencias', { params })).data;
  },
  async buscarPorId(id: string): Promise<OcorrenciaDetalhe> {
    return (await api.get<OcorrenciaDetalhe>(`/v1/ocorrencias/${id}`)).data;
  },
  async validar(id: string): Promise<OcorrenciaDetalhe> {
    return (await api.post<OcorrenciaDetalhe>(`/v1/ocorrencias/${id}/validar`)).data;
  },
  async devolver(id: string, justificativa: string): Promise<OcorrenciaDetalhe> {
    return (await api.post<OcorrenciaDetalhe>(`/v1/ocorrencias/${id}/devolver`, { justificativa })).data;
  },
  async rejeitar(id: string, justificativa: string): Promise<OcorrenciaDetalhe> {
    return (await api.post<OcorrenciaDetalhe>(`/v1/ocorrencias/${id}/rejeitar`, { justificativa })).data;
  },
  async corrigir(id: string, data: CorrigirOcorrenciaRequest): Promise<OcorrenciaDetalhe> {
    return (await api.put<OcorrenciaDetalhe>(`/v1/ocorrencias/${id}`, data)).data;
  },
  async reenviar(id: string): Promise<OcorrenciaDetalhe> {
    return (await api.post<OcorrenciaDetalhe>(`/v1/ocorrencias/${id}/reenviar`)).data;
  },
  async encerrar(id: string, desfecho: string): Promise<OcorrenciaDetalhe> {
    return (await api.post<OcorrenciaDetalhe>(`/v1/ocorrencias/${id}/encerrar`, { desfecho })).data;
  },
};
