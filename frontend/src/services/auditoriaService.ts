import { api } from './api';
import type { AcaoAuditada, FiltroAuditoria, PaginaAuditoria } from '../types/api';
import { nomeDoArquivo, salvarBlob } from '../utils/download';

export const auditoriaService = {
  /** Catálogo das ações auditadas, usado nos filtros da trilha. */
  async catalogo(): Promise<AcaoAuditada[]> {
    return (await api.get<AcaoAuditada[]>('/v1/auditoria/catalogo')).data;
  },
  /** Uma página da trilha (mais recentes primeiro), com o total para a paginação. */
  async listar(filtro?: FiltroAuditoria): Promise<PaginaAuditoria> {
    return (await api.get<PaginaAuditoria>('/v1/auditoria', { params: filtro })).data;
  },
  /** CSV da trilha filtrada (CPF mascarado no backend); a própria exportação entra na auditoria. */
  async exportarCsv(filtro?: FiltroAuditoria): Promise<void> {
    const resposta = await api.get<Blob>('/v1/auditoria/exportar', { params: { ...filtro, formato: 'csv' }, responseType: 'blob' });
    salvarBlob(resposta.data, nomeDoArquivo(resposta.headers['content-disposition'], 'auditoria.csv'));
  },
};
