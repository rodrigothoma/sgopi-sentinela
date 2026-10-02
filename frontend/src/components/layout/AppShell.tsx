import React, { useState } from 'react';
import { Outlet, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Sidebar } from './Sidebar';
import { LogoSgopi } from '../common/LogoSgopi';

export const AppShell: React.FC = () => {
  const { t } = useTranslation('common');
  const [mobileAberta, setMobileAberta] = useState(false);

  return (
    <div className="shell-with-sidebar">
      <Sidebar
        mobileAberta={mobileAberta}
        onFecharMobile={() => setMobileAberta(false)}
      />
      <div className="shell-main-area">
        <header className="mobile-topbar">
          <button
            type="button"
            className="mobile-menu-btn"
            onClick={() => setMobileAberta(true)}
            aria-label="Abrir menu de navegação"
          >
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="3" y1="12" x2="21" y2="12" />
              <line x1="3" y1="6" x2="21" y2="6" />
              <line x1="3" y1="18" x2="21" y2="18" />
            </svg>
          </button>
          <Link to="/" className="brand" title="Voltar ao Portal Público">
            <LogoSgopi size={24} color="var(--primary)" />
            <span>{t('app.title')}</span>
          </Link>
          <div style={{ width: 36 }} aria-hidden="true" />
        </header>
        <main className="content">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default AppShell;

