import { api } from './api';
import type { Indicadores } from '../types/api';

export const indicadoresService = {
  /** KPIs do período (sugestão #11); o fuso do navegador define as faixas horárias. */
  async obter(de: string, ate: string): Promise<Indicadores> {
    const fuso = Intl.DateTimeFormat().resolvedOptions().timeZone || 'America/Sao_Paulo';
    return (await api.get<Indicadores>('/v1/indicadores', { params: { de, ate, fuso } })).data;
  },
};
