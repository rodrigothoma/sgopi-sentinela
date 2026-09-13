import type { Usuario } from '../types/api';

const CHAVE = 'sgopi.sessao';

interface SessaoArmazenada { token: string; expira_em: string; usuario: Usuario }

/** Sessão em sessionStorage (limpa ao fechar a aba). Token JWT de turno — 8 h. */
export const sessao = {
  ler(): SessaoArmazenada | null {
    try {
      const raw = sessionStorage.getItem(CHAVE);
      if (!raw) return null;
      const s = JSON.parse(raw) as SessaoArmazenada;
      if (new Date(s.expira_em).getTime() <= Date.now()) {
        sessionStorage.removeItem(CHAVE);
        return null;
      }
      return s;
    } catch {
      return null;
    }
  },
  gravar(s: SessaoArmazenada) {
    sessionStorage.setItem(CHAVE, JSON.stringify(s));
  },
  limpar() {
    sessionStorage.removeItem(CHAVE);
  },
  token(): string | null {
    return sessao.ler()?.token ?? null;
  },
  idioma(): string {
    try {
      return localStorage.getItem('sgopi.idioma') || 'pt';
    } catch {
      return 'pt';
    }
  },
};
