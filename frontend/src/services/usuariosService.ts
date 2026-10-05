import { api } from './api';
import type { CadastrarUsuarioRequest, Papel, Usuario, UsuarioGestao } from '../types/api';

export const usuariosService = {
  /** Efetivo ativo (nome, login e papel) — alimenta a tela inicial. */
  async listar(): Promise<Usuario[]> {
    return (await api.get<Usuario[]>('/v1/usuarios')).data;
  },
  /** Somente SUPERVISOR: todos os usuários, inclusive inativos (sugestão #13). */
  async listarGestao(): Promise<UsuarioGestao[]> {
    return (await api.get<UsuarioGestao[]>('/v1/usuarios/gestao')).data;
  },
  async cadastrar(dados: CadastrarUsuarioRequest): Promise<UsuarioGestao> {
    return (await api.post<UsuarioGestao>('/v1/usuarios', dados)).data;
  },
  async alterarPapel(id: string, papel: Papel): Promise<UsuarioGestao> {
    return (await api.patch<UsuarioGestao>(`/v1/usuarios/${id}/papel`, { papel })).data;
  },
  async desativar(id: string, motivo?: string): Promise<UsuarioGestao> {
    return (await api.post<UsuarioGestao>(`/v1/usuarios/${id}/desativar`, { motivo: motivo || null })).data;
  },
  async reativar(id: string): Promise<UsuarioGestao> {
    return (await api.post<UsuarioGestao>(`/v1/usuarios/${id}/reativar`, {})).data;
  },
};
