import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import type { Papel } from '../types/api';

/** RNF02: a UI esconde/bloqueia rotas por papel; a autorização real é do backend. */
export const RequireRole: React.FC<{ papeis?: Papel[]; children: React.ReactElement }> = ({ papeis, children }) => {
  const { usuario, tem } = useAuth();
  const location = useLocation();
  if (!usuario) return <Navigate to="/login" replace state={{ de: location.pathname }} />;
  if (papeis && !tem(...papeis)) return <Navigate to="/" replace />;
  return children;
};

export function rotaInicial(_papel: Papel): string {
  // Todos os papéis entram pela tela inicial (resumo operacional); a navegação por papel fica no AppShell.
  return '/inicio';
}
