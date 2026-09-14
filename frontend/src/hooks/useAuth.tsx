import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { authService } from '../services/authService';
import { sessao } from '../services/sessao';
import type { Papel, Usuario } from '../types/api';

interface AuthContexto {
  usuario: Usuario | null;
  entrar: (login: string, senha: string) => Promise<Usuario>;
  sair: () => void;
  tem: (...papeis: Papel[]) => boolean;
}

const Ctx = createContext<AuthContexto | null>(null);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [usuario, setUsuario] = useState<Usuario | null>(() => sessao.ler()?.usuario ?? null);

  const sair = useCallback(() => {
    sessao.limpar();
    setUsuario(null);
  }, []);

  useEffect(() => {
    window.addEventListener('sgopi:sessao-expirada', sair);
    return () => window.removeEventListener('sgopi:sessao-expirada', sair);
  }, [sair]);

  const entrar = useCallback(async (login: string, senha: string) => {
    const r = await authService.login(login, senha);
    sessao.gravar({ token: r.access_token, expira_em: r.expira_em, usuario: r.usuario });
    setUsuario(r.usuario);
    return r.usuario;
  }, []);

  const valor = useMemo<AuthContexto>(
    () => ({ usuario, entrar, sair, tem: (...papeis) => !!usuario && papeis.includes(usuario.papel) }),
    [usuario, entrar, sair],
  );
  return <Ctx.Provider value={valor}>{children}</Ctx.Provider>;
};

export function useAuth(): AuthContexto {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error('useAuth fora do AuthProvider');
  return ctx;
}
