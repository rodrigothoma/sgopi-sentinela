import { api } from './api';
import type { FiltroAuditoria, RegistroAuditoria } from '../types/api';
import { nomeDoArquivo, salvarBlob } from '../utils/download';

export const auditoriaService = {
  async listar(filtro?: FiltroAuditoria): Promise<RegistroAuditoria[]> {
    return (await api.get<RegistroAuditoria[]>('/v1/auditoria', { params: filtro })).data;
  },
  /** CSV da trilha filtrada (CPF mascarado no backend); a própria exportação entra na auditoria. */
  async exportarCsv(filtro?: FiltroAuditoria): Promise<void> {
    const resposta = await api.get<Blob>('/v1/auditoria/exportar', { params: { ...filtro, formato: 'csv' }, responseType: 'blob' });
    salvarBlob(resposta.data, nomeDoArquivo(resposta.headers['content-disposition'], 'auditoria.csv'));
  },
};
