import React from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../hooks/useAuth';

export const AppShell: React.FC = () => {
  const { t, i18n } = useTranslation('common');
  const { usuario, sair, tem } = useAuth();
  const navigate = useNavigate();

  const trocarIdioma = (lng: string) => {
    i18n.changeLanguage(lng);
    try {
      localStorage.setItem('sgopi.idioma', lng);
    } catch {
      /* sem persistência */
    }
  };

  return (
    <div className="shell">
      <header className="topbar">
        <div className="brand">🛡️ {t('app.title')}</div>
        <nav>
          <NavLink to="/inicio">{t('nav.inicio')}</NavLink>
          {tem('AGENTE') && <NavLink to="/registrar">{t('nav.registrar')}</NavLink>}
          {tem('AGENTE') && <NavLink to="/minhas">{t('nav.minhas')}</NavLink>}
          {tem('DELEGADO', 'SUPERVISOR') && <NavLink to="/fila">{t('nav.fila')}</NavLink>}
          {tem('OPERADOR_CENTRAL', 'SUPERVISOR', 'DELEGADO') && <NavLink to="/painel">{t('nav.painel')}</NavLink>}
          {tem('OPERADOR_CENTRAL', 'SUPERVISOR') && <NavLink to="/frota">{t('nav.frota')}</NavLink>}
        </nav>
        <div className="userbox">
          <select aria-label={t('idioma')} value={i18n.language.slice(0, 2)} onChange={(e) => trocarIdioma(e.target.value)}>
            <option value="pt">PT</option>
            <option value="en">EN</option>
          </select>
          {usuario && (
            <span className="user">
              <strong>{usuario.nome}</strong> · <span className="pill">{t(`papel.${usuario.papel}`)}</span>
            </span>
          )}
          <button
            className="btn btn-ghost"
            onClick={() => {
              sair();
              navigate('/login');
            }}
          >
            {t('actions.sair')}
          </button>
        </div>
      </header>
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
};
