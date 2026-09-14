import { api } from './api';
import type { Usuario } from '../types/api';

export const usuariosService = {
  /** Efetivo ativo (nome, login e papel) — alimenta a tela inicial. */
  async listar(): Promise<Usuario[]> {
    return (await api.get<Usuario[]>('/v1/usuarios')).data;
  },
};
