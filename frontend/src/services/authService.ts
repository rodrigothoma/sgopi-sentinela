import { api } from './api';
import type { LoginResponse } from '../types/api';

export const authService = {
  async login(login: string, senha: string): Promise<LoginResponse> {
    const { data } = await api.post<LoginResponse>('/v1/auth/login', { login, senha });
    return data;
  },
};
