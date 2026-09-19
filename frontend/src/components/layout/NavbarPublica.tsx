import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { LogoSgopi } from '../common/LogoSgopi';
import { useTheme } from '../../hooks/useTheme';

export const NavbarPublica: React.FC = () => {
  const { t, i18n } = useTranslation('common');
  const { theme, toggleTheme } = useTheme();
  const location = useLocation();

  const trocarIdioma = (lng: string) => {
    i18n.changeLanguage(lng);
    try {
      localStorage.setItem('sgopi.idioma', lng);
    } catch {
      /* sem persistência */
    }
  };

  return (
    <header className="topbar">
      <Link to="/" className="brand">
        <LogoSgopi size={32} color="var(--primary)" />
        <span>{t('app.title')}</span>
      </Link>

      <nav>
        <Link to="/" className={location.pathname === '/' ? 'active' : ''}>
          Início
        </Link>
        <Link to="/registrar-cidadao" className={location.pathname === '/registrar-cidadao' ? 'active' : ''}>
          Registrar Ocorrência
        </Link>
        <Link to="/consulta" className={location.pathname === '/consulta' ? 'active' : ''}>
          Consultar Protocolo
        </Link>
      </nav>

      <div className="userbox">
        <select
          aria-label={t('idioma')}
          value={i18n.language.slice(0, 2)}
          onChange={(e) => trocarIdioma(e.target.value)}
        >
          <option value="pt">🇧🇷 PT</option>
          <option value="en">🇺🇸 EN</option>
        </select>

        <button
          type="button"
          className="btn-icon"
          onClick={toggleTheme}
          title={`Mudar para tema ${theme === 'dark' ? 'claro' : 'escuro'}`}
          aria-label="Alternar tema"
        >
          {theme === 'dark' ? '☀️' : '🌙'}
        </button>

        <Link to="/login" className="btn btn-primary" style={{ padding: '8px 16px', fontSize: '0.88rem' }}>
          🛡️ Acesso Policial
        </Link>
      </div>
    </header>
  );
};
