import React, { useState } from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Sidebar } from './Sidebar';
import { LogoSgopi } from '../common/LogoSgopi';
import { useAuth } from '../../hooks/useAuth';
import { useTempoRealListener } from '../../hooks/useTempoReal';
import { useToast } from '../../hooks/useToast';
import type { EventoTempoReal } from '../../types/api';

export const AppShell: React.FC = () => {
  const { t } = useTranslation(['common', 'painel']);
  const [mobileAberta, setMobileAberta] = useState(false);
  const { usuario, tem } = useAuth();
  const { avisar } = useToast();
  const location = useLocation();

  // Toasts da casca (issue #68): o WS já filtra a audiência de cada evento; aqui
  // só refinamos o destinatário local (autor da validação; papel da chegada) e
  // evitamos duplicar o toast de chegada que o Painel Tático já exibe em /painel.
  useTempoRealListener({
    onEvento: (e: EventoTempoReal) => {
      const d = e.dados as Record<string, unknown>;
      switch (e.tipo) {
        case 'OcorrenciaCriada':
          avisar(
            t('common:tempo_real.nova_ocorrencia', {
              protocolo: String(d.numero_protocolo ?? ''),
              natureza: String(d.natureza ?? ''),
            }),
            'info',
          );
          break;
        case 'OcorrenciaValidada':
          if (d.agente_policial_id && d.agente_policial_id === usuario?.id) {
            avisar(t('common:tempo_real.validada', { protocolo: String(d.numero_protocolo ?? '') }), 'sucesso');
          }
          break;
        case 'ViaturaChegouAoLocal':
          if (location.pathname !== '/painel' && (tem('OPERADOR_CENTRAL') || tem('SUPERVISOR'))) {
            avisar(
              t('painel:chegada.mensagem', {
                prefixo: String(d.prefixo ?? ''),
                protocolo: String(d.numero_protocolo ?? ''),
                ordem: String(d.numero_ordem ?? ''),
              }),
              'sucesso',
            );
          }
          break;
        default:
          break;
      }
    },
  });

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
            aria-label={t('common:sidebar.abrir_menu')}
          >
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="3" y1="12" x2="21" y2="12" />
              <line x1="3" y1="6" x2="21" y2="6" />
              <line x1="3" y1="18" x2="21" y2="18" />
            </svg>
          </button>
          <Link to="/" className="brand" title={t('common:sidebar.voltar_portal')}>
            <LogoSgopi size={24} color="var(--primary)" />
            <span>{t('common:app.title')}</span>
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
