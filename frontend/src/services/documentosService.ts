import { api } from './api';
import type { DocumentoAutenticado } from '../types/api';

/** RF08 / UC08 — portal público de autenticação de documentos (não exige login). */
export const documentosService = {
  /** `codigo` é a chave de 24 caracteres (hífens opcionais) ou o hash SHA-256 impresso no documento. */
  async autenticar(codigo: string): Promise<DocumentoAutenticado> {
    return (await api.get<DocumentoAutenticado>(`/v1/publico/documentos/${encodeURIComponent(codigo.trim())}`)).data;
  },
};
