import axios, { AxiosError } from 'axios';
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
export function mensagemDeErro(error: unknown, fallback = 'Erro inesperado'): string {
  if (axios.isAxiosError<ErroApi>(error)) {
    const corpo = error.response?.data;
    if (corpo?.detail) return corpo.request_id ? `${corpo.detail} (ref. ${corpo.request_id.slice(0, 8)})` : corpo.detail;
    if (!error.response) return 'Servidor indisponível';
  }
  return fallback;
}
