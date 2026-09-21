import React from 'react';
import { NavLink, Outlet, useNavigate, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../hooks/useAuth';
import { LogoSgopi } from '../common/LogoSgopi';
import { ThemeToggle } from '../common/ThemeToggle';
import { GlideSelect, GlideSelectOption } from '../common/GlideSelect';
import { Button } from '../common/Button';
import { trocarIdiomaGlobal } from '../../i18n';

const OPCOES_IDIOMA: GlideSelectOption[] = [
  { value: 'pt', label: 'PT', tag: 'Português' },
  { value: 'en', label: 'EN', tag: 'English' },
];

export const AppShell: React.FC = () => {
  const { t, i18n } = useTranslation('common');
  const { usuario, sair, tem } = useAuth();
  const navigate = useNavigate();

  const idiomaAtual = i18n.language ? i18n.language.slice(0, 2) : 'pt';

  return (
    <div className="shell">
      <header className="topbar">
        <Link to="/" className="brand" title="Voltar ao Portal Público">
          <LogoSgopi size={28} color="var(--primary)" />
          <span>{t('app.title')}</span>
        </Link>
        <nav>
          {tem('AGENTE') && <NavLink to="/registrar">{t('nav.registrar')}</NavLink>}
          {tem('AGENTE') && <NavLink to="/minhas">{t('nav.minhas')}</NavLink>}
          {tem('DELEGADO', 'SUPERVISOR') && <NavLink to="/fila">{t('nav.fila')}</NavLink>}
          {tem('OPERADOR_CENTRAL', 'SUPERVISOR', 'DELEGADO') && <NavLink to="/painel">{t('nav.painel')}</NavLink>}
          {tem('OPERADOR_CENTRAL', 'SUPERVISOR') && <NavLink to="/frota">{t('nav.frota')}</NavLink>}
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
          {usuario && (
            <div className="user-profile-header">
              <span className="user-name">{usuario.nome}</span>
              <span className="user-role">{t(`papel.${usuario.papel}`)}</span>
            </div>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              sair();
              navigate('/login');
            }}
          >
            {t('actions.sair')}
          </Button>
        </div>
      </header>
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
};

export default AppShell;
