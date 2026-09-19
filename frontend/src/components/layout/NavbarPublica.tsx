import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { LogoSgopi } from '../common/LogoSgopi';
import { ThemeToggle } from '../common/ThemeToggle';

export const NavbarPublica: React.FC = () => {
  const { t, i18n } = useTranslation('common');
  const location = useLocation();

  const trocarIdioma = (lng: string) => {
    i18n.changeLanguage(lng);
    try {
      localStorage.setItem('sgopi.idioma', lng);
    } catch {
      /* sem persistência */
    }
  };

  const isActive = (path: string) => location.pathname === path ? 'active' : '';

  return (
    <header className="topbar">
      <Link to="/" className="brand">
        <LogoSgopi size={28} color="var(--primary)" />
        <span>{t('app.title')}</span>
      </Link>

      <nav>
        <Link to="/" className={isActive('/')}>Início</Link>
        <Link to="/registrar-cidadao" className={isActive('/registrar-cidadao')}>Registrar Ocorrência</Link>
        <Link to="/consulta" className={isActive('/consulta')}>Consultar Protocolo</Link>
      </nav>

      <div className="userbox">
        <select
          aria-label={t('idioma')}
          value={i18n.language.slice(0, 2)}
          onChange={(e) => trocarIdioma(e.target.value)}
          style={{ width: 'auto', padding: '4px 8px', fontSize: '0.85rem' }}
        >
          <option value="pt">PT</option>
          <option value="en">EN</option>
        </select>

        <ThemeToggle />

        <Link to="/login" className="btn btn-secondary" style={{ padding: '7px 14px', fontSize: '0.88rem' }}>
          Acesso Policial
        </Link>
      </div>
    </header>
  );
};
