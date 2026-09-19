import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { NavbarPublica } from '../components/layout/NavbarPublica';
import { SplitFlapText } from '../components/common/SplitFlapText';
import { LogoSgopi } from '../components/common/LogoSgopi';
import { useTheme } from '../hooks/useTheme';

export const LandingPage: React.FC = () => {
  const { t } = useTranslation('common');
  const { theme } = useTheme();

  return (
    <div className="portal-wrap">
      <NavbarPublica />

      <main className="landing-hero">
        <div className="hero-badge-pill">
          <span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '50%', background: 'var(--ok)' }} />
          SISTEMA INTEGRADO DE SEGURANÇA PÚBLICA
        </div>

        <div className="hero-flap-wrapper">
          <SplitFlapText
            words={['SENTINELA ONLINE', 'PORTAL CIDADAO', 'PRONTIDAO TOTAL', 'SISTEMA INTEGRADO']}
            padTo={16}
            fontSize={36}
            tileRadius={6}
            gap={4}
            tileColor={theme === 'dark' ? '#131b2e' : '#e2e8f0'}
            textColor={theme === 'dark' ? '#f8fafc' : '#0f172a'}
          />
        </div>

        <p className="hero-subtitle">
          Canal oficial e unificado para registro ágil de ocorrências pelo cidadão, triagem técnica
          pela autoridade policial e monitoramento tático georreferenciado em tempo real.
        </p>

        <section className="action-cards-grid">
          <Link to="/registrar-cidadao" className="action-card">
            <div className="action-card-icon">📝</div>
            <h3>Registrar Ocorrência</h3>
            <p>
              Comunique furtos, extravios, ameaças e outros fatos de forma rápida, sem filas e com
              localização no mapa.
            </p>
            <div className="action-card-footer">
              Registrar agora <span>→</span>
            </div>
          </Link>

          <Link to="/consulta" className="action-card">
            <div className="action-card-icon">🔍</div>
            <h3>Consultar Protocolo</h3>
            <p>
              Acompanhe a situação e o andamento da sua ocorrência em tempo real utilizando o código
              do protocolo oficial.
            </p>
            <div className="action-card-footer">
              Verificar status <span>→</span>
            </div>
          </Link>

          <Link to="/login" className="action-card">
            <div className="action-card-icon">🛡️</div>
            <h3>Painel Operacional</h3>
            <p>
              Acesso restrito para Agentes de campo, Delegados de triagem e Operadores da Central de
              Despacho.
            </p>
            <div className="action-card-footer">
              Entrar no sistema <span>→</span>
            </div>
          </Link>
        </section>
      </main>

      <footer style={{ marginTop: 'auto', borderTop: '1px solid var(--line)', padding: '24px', textAlign: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10, marginBottom: 8 }}>
          <LogoSgopi size={22} color="var(--primary)" />
          <strong style={{ fontSize: '0.9rem', color: 'var(--ink)' }}>{t('app.title')}</strong>
        </div>
        <p className="muted small" style={{ margin: 0 }}>
          Engenharia de Software — Unipampa Campus Alegrete · Resolução de Problemas IV (AL0343)
        </p>
      </footer>
    </div>
  );
};
