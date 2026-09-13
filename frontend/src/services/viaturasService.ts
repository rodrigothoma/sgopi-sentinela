import { api } from './api';
import type { SituacaoViatura, StatusSimulador, Viatura } from '../types/api';

export const viaturasService = {
  async listar(): Promise<Viatura[]> {
    return (await api.get<Viatura[]>('/v1/viaturas')).data;
  },
  async cadastrar(prefixo: string, placa: string): Promise<Viatura> {
    return (await api.post<Viatura>('/v1/viaturas', { prefixo, placa })).data;
  },
  async alterarSituacao(id: string, situacao: Extract<SituacaoViatura, 'DISPONIVEL' | 'INDISPONIVEL'>): Promise<Viatura> {
    return (await api.patch<Viatura>(`/v1/viaturas/${id}/situacao`, { situacao })).data;
  },
  async simulador(): Promise<StatusSimulador> {
    return (await api.get<StatusSimulador>('/v1/simulador')).data;
  },
  async ligarSimulador(): Promise<StatusSimulador> {
    return (await api.post<StatusSimulador>('/v1/simulador/ligar')).data;
  },
  async desligarSimulador(): Promise<StatusSimulador> {
    return (await api.post<StatusSimulador>('/v1/simulador/desligar')).data;
  },
};
