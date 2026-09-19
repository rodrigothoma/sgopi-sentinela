import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { LogoSgopi } from '../common/LogoSgopi';
import { ThemeToggle } from '../common/ThemeToggle';
import { GlideSelect, GlideSelectOption } from '../common/GlideSelect';
import { Button } from '../common/Button';
import { trocarIdiomaGlobal } from '../../i18n';

const OPCOES_IDIOMA: GlideSelectOption[] = [
  { value: 'pt', label: 'PT', tag: 'Português' },
  { value: 'en', label: 'EN', tag: 'English' },
];

export const NavbarPublica: React.FC = () => {
  const { t, i18n } = useTranslation('common');
  const location = useLocation();

  const isActive = (path: string) => (location.pathname === path ? 'active' : '');
  const idiomaAtual = i18n.language ? i18n.language.slice(0, 2) : 'pt';

  return (
    <header className="topbar">
      <Link to="/" className="brand">
        <LogoSgopi size={28} color="var(--primary)" />
        <span>{t('app.title')}</span>
      </Link>

      <nav>
        <Link to="/" className={isActive('/')}>
          Início
        </Link>
        <Link to="/registrar-cidadao" className={isActive('/registrar-cidadao')}>
          Registrar Ocorrência
        </Link>
        <Link to="/consulta" className={isActive('/consulta')}>
          Consultar Protocolo
        </Link>
      </nav>

      <div className="userbox">
        <GlideSelect
          options={OPCOES_IDIOMA}
          value={idiomaAtual}
          onChange={(val) => trocarIdiomaGlobal(val)}
          size="sm"
          menuWidth={140}
          showTags
          ariaLabel={t('idioma')}
        />

        <ThemeToggle />

        <Button to="/login" variant="outline" size="sm">
          Acesso Policial
        </Button>
      </div>
    </header>
  );
};

export default NavbarPublica;
