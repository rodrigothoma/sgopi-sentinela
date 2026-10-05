import { api } from './api';
import type {
  CorrigirOcorrenciaRequest, Evidencia, EventoLinhaDoTempo, FiltrosOcorrencias, PrioridadeOcorrencia, IntegridadeEvidencia, OcorrenciaCriada, OcorrenciaDetalhe, OcorrenciaResumo, Pagina,
  RegistrarOcorrenciaRequest, StatusOcorrencia,
} from '../types/api';
import { nomeDoArquivo, salvarBlob } from '../utils/download';
import { aplicarFiltrosNaApi } from '../utils/filtrosOcorrencias';

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
    salvarBlob(resposta.data, evidencia.nome_original);
  },
  /** Padrão: mais antiga primeiro (fila do UC04); ``maisRecentesPrimeiro`` inverte ANTES de paginar. */
  async listar(
    status: StatusOcorrencia[] = [], limit = 50, offset = 0, maisRecentesPrimeiro = false, filtros?: FiltrosOcorrencias,
    ordenarPorPrioridade = false,
  ): Promise<Pagina<OcorrenciaResumo>> {
    const params = new URLSearchParams();
    status.forEach((s) => params.append('status', s));
    params.set('limit', String(limit));
    params.set('offset', String(offset));
    if (maisRecentesPrimeiro) params.set('mais_recentes_primeiro', 'true');
    if (ordenarPorPrioridade) params.set('ordenar_por_prioridade', 'true');
    aplicarFiltrosNaApi(params, filtros);
    return (await api.get<Pagina<OcorrenciaResumo>>('/v1/ocorrencias', { params })).data;
  },
  /** CSV da listagem filtrada — somente DELEGADO/SUPERVISOR; a exportação é auditada no backend. */
  async exportarCsv(status: StatusOcorrencia[] = [], filtros?: FiltrosOcorrencias): Promise<void> {
    const params = new URLSearchParams({ formato: 'csv' });
    status.forEach((s) => params.append('status', s));
    aplicarFiltrosNaApi(params, filtros);
    const resposta = await api.get<Blob>('/v1/ocorrencias/exportar', { params, responseType: 'blob' });
    salvarBlob(resposta.data, nomeDoArquivo(resposta.headers['content-disposition'], 'ocorrencias.csv'));
  },
  async buscarPorId(id: string): Promise<OcorrenciaDetalhe> {
    return (await api.get<OcorrenciaDetalhe>(`/v1/ocorrencias/${id}`)).data;
  },
  /** Somente DELEGADO; justificativa obrigatória e auditada (sugestão #7). */
  async redefinirPrioridade(id: string, prioridade: PrioridadeOcorrencia, justificativa: string): Promise<OcorrenciaDetalhe> {
    return (await api.post<OcorrenciaDetalhe>(`/v1/ocorrencias/${id}/prioridade`, { prioridade, justificativa })).data;
  },
  /** Status, despachos, evidências, apreensões, inquérito e laudos em ordem cronológica (sugestão #12). */
  async linhaDoTempo(id: string): Promise<EventoLinhaDoTempo[]> {
    return (await api.get<EventoLinhaDoTempo[]>(`/v1/ocorrencias/${id}/linha-do-tempo`)).data;
  },
  async validar(id: string, despacho?: string): Promise<OcorrenciaDetalhe> {
    return (await api.post<OcorrenciaDetalhe>(`/v1/ocorrencias/${id}/validar`, { despacho: despacho || null })).data;
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
  /** Somente DELEGADO; motivo obrigatório (RF20). */
  async arquivar(id: string, motivo: string): Promise<OcorrenciaDetalhe> {
    return (await api.post<OcorrenciaDetalhe>(`/v1/ocorrencias/${id}/arquivar`, { motivo })).data;
  },
  /** Exclusão lógica — somente DELEGADO; motivo obrigatório (RF20). */
  async excluir(id: string, motivo: string): Promise<OcorrenciaDetalhe> {
    return (await api.post<OcorrenciaDetalhe>(`/v1/ocorrencias/${id}/excluir`, { motivo })).data;
  },
};
