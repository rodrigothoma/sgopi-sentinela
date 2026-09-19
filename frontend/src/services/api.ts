import axios, { AxiosError } from 'axios';
import i18n from '../i18n';
import type { ErroApi } from '../types/api';
import { sessao } from './sessao';

/**
 * Vazio por padrão: as requisições ficam relativas ao próprio origin e, em dev,
 * passam pelo proxy do Vite (vite.config.ts) — sem CORS e independente da porta
 * em que o Vite subiu. Defina VITE_API_BASE_URL apenas quando o backend estiver
 * em outro host/porta e não houver proxy na frente.
 */
export const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL ?? '';

export const api = axios.create({ baseURL: API_BASE_URL });

api.interceptors.request.use((config) => {
  const token = sessao.token();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  config.headers['Accept-Language'] = sessao.idioma();
  return config;
});

api.interceptors.response.use(
  (r) => r,
  (error: AxiosError<ErroApi>) => {
    if (error.response?.status === 401 && sessao.token()) {
      sessao.limpar();
      window.dispatchEvent(new Event('sgopi:sessao-expirada'));
    }
    return Promise.reject(error);
  },
);

/** Extrai a mensagem i18n padronizada do backend ({detail, code, request_id}). */
export function mensagemDeErro(error: unknown, fallback?: string): string {
  const defaultFallback = fallback ?? i18n.t('errors.unexpected', 'Erro inesperado');
  if (axios.isAxiosError<ErroApi>(error)) {
    const corpo = error.response?.data;
    if (corpo?.detail) return corpo.request_id ? `${corpo.detail} (ref. ${corpo.request_id.slice(0, 8)})` : corpo.detail;
    if (!error.response) return i18n.t('errors.unavailable', 'Servidor indisponível');
  }
  return defaultFallback;
}

export interface RegistrarOcorrenciaPublicaPayload {
  nome_solicitante: string;
  natureza: string;
  descricao: string;
  localizacao: string;
  latitude: number;
  longitude: number;
  data_hora_fato: string;
  documento?: string;
}

export interface OcorrenciaPublicaResponse {
  ocorrencia_id: string;
  numero_protocolo: string;
  status: string;
  criada_em: string;
}

export interface ConsultaPublicaResponse {
  numero_protocolo: string;
  status: string;
  natureza: string;
  localizacao: string;
  criada_em: string;
  desfecho?: string | null;
}

export async function registrarOcorrenciaPublica(payload: RegistrarOcorrenciaPublicaPayload): Promise<OcorrenciaPublicaResponse> {
  const { data } = await api.post<OcorrenciaPublicaResponse>('/v1/ocorrencias/publico', payload);
  return data;
}

export async function consultarOcorrenciaPublica(protocolo: string): Promise<ConsultaPublicaResponse> {
  const { data } = await api.get<ConsultaPublicaResponse>(`/v1/ocorrencias/publico/${encodeURIComponent(protocolo.trim())}`);
  return data;
}
