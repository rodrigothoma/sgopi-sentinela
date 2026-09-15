import { api } from './api';
import type { DocumentoAutenticado } from '../types/api';

/** Portal público (RF08): não exige sessão; o interceptor só anexa o token se houver um. */
export const documentosService = {
  async autenticar(chave: string): Promise<DocumentoAutenticado> {
    return (await api.get<DocumentoAutenticado>(`/v1/publico/documentos/${encodeURIComponent(chave.trim())}`)).data;
  },
  /** URL absoluta da página pública — é o conteúdo do QR Code impresso no documento. */
  urlPublica(chave: string): string {
    return `${window.location.origin}/autenticar/${chave}`;
  },
};
