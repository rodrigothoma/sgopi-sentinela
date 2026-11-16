import { api } from './api';
import type { SituacaoViatura, StatusSimuladorCompleto, Viatura } from '../types/api';

export const viaturasService = {
  async listar(): Promise<Viatura[]> {
    return (await api.get<Viatura[]>('/v1/viaturas')).data;
  },
  async cadastrar(prefixo: string, placa: string, responsavel: string | null = null): Promise<Viatura> {
    return (await api.post<Viatura>('/v1/viaturas', { prefixo, placa, responsavel })).data;
  },
  async editar(id: string, cadastro: { prefixo: string; placa: string; responsavel: string | null; versao: number }): Promise<Viatura> {
    return (await api.patch<Viatura>(`/v1/viaturas/${id}`, cadastro)).data;
  },
  async excluir(id: string, versao: number): Promise<void> {
    await api.delete(`/v1/viaturas/${id}`, { params: { versao } });
  },
  async alterarSituacao(id: string, situacao: Extract<SituacaoViatura, 'DISPONIVEL' | 'INDISPONIVEL'>): Promise<Viatura> {
    return (await api.patch<Viatura>(`/v1/viaturas/${id}/situacao`, { situacao })).data;
  },
  async simulador(): Promise<StatusSimuladorCompleto> {
    return (await api.get<StatusSimuladorCompleto>('/v1/simulador')).data;
  },
  async ligarSimulador(): Promise<StatusSimuladorCompleto> {
    return (await api.post<StatusSimuladorCompleto>('/v1/simulador/ligar')).data;
  },
  async desligarSimulador(): Promise<StatusSimuladorCompleto> {
    return (await api.post<StatusSimuladorCompleto>('/v1/simulador/desligar')).data;
  },
};
