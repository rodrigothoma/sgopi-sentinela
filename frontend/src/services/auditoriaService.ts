import { api } from './api';
import type { FiltroAuditoria, RegistroAuditoria } from '../types/api';

export const auditoriaService = {
  async listar(filtro?: FiltroAuditoria): Promise<RegistroAuditoria[]> {
    return (await api.get<RegistroAuditoria[]>('/v1/auditoria', { params: filtro })).data;
  },
};
