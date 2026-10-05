import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { NavbarPublica } from '../components/layout/NavbarPublica';
import { SplitFlapText } from '../components/common/SplitFlapText';
import { LogoSgopi } from '../components/common/LogoSgopi';
import { WebThreads } from '../components/common/WebThreads';
import { Button } from '../components/common/Button';
import { useTheme } from '../hooks/useTheme';

/* Ícones SVG simples para os cards — sem emojis */
const IconDocument: React.FC = () => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="22" height="22"
    fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"
    aria-hidden="true">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline points="14 2 14 8 20 8" />
    <line x1="16" y1="13" x2="8" y2="13" />
    <line x1="16" y1="17" x2="8" y2="17" />
    <line x1="10" y1="9" x2="8" y2="9" />
  </svg>
);

const IconSearch: React.FC = () => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="22" height="22"
    fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"
    aria-hidden="true">
    <circle cx="11" cy="11" r="8" />
    <line x1="21" y1="21" x2="16.65" y2="16.65" />
  </svg>
);

const IconShield: React.FC = () => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="22" height="22"
    fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"
    aria-hidden="true">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
  </svg>
);

export const LandingPage: React.FC = () => {
  const { t } = useTranslation('common');
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  const splitWords = [
    t('landing.split_word_1'),
    t('landing.split_word_2'),
    t('landing.split_word_3'),
    t('landing.split_word_4'),
  ];

  return (
    <div className="portal-wrap">
      <NavbarPublica />

      {/* ── Hero ─────────────────────────────────────────────────────── */}
      <main className="landing-hero" style={{ position: 'relative', overflow: 'hidden' }}>
        {/* Fundo dinâmico WebThreads oficial React Bits via OGL */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            width: '100%',
            height: '100%',
            zIndex: 0,
            opacity: isDark ? 0.30 : 0.38,
            pointerEvents: 'none',
            maskImage: 'linear-gradient(to bottom, black 65%, transparent 100%)',
            WebkitMaskImage: 'linear-gradient(to bottom, black 65%, transparent 100%)',
          }}
          aria-hidden="true"
        >
          <WebThreads
            color1={isDark ? '#94a3b8' : '#0515d3'}
            color2={isDark ? '#cbd5e1' : '#0b4aaf'}
            color3={isDark ? '#f1f5f9' : '#70a5ff'}
            speed={0.18}
            threadCount={6}
            frequency={4.2}
            spread={0.36}
            taper={0.9}
            position={0.48}
            fanMode="center"
            glow={isDark ? 0.016 : 0.015}
            falloff={0.52}
            thickness={isDark ? 1.5 : 1.4}
            brightness={isDark ? 0.55 : 0.42}
            opacity={isDark ? 0.72 : 0.65}
            mirror={true}
            shimmer={true}
            grain={true}
            grainIntensity={0.03}
            mouseInteraction={true}
            mouseStrength={0.3}
          />
        </div>

        <div style={{ position: 'relative', zIndex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', width: '100%' }}>
          <p className="hero-label">{t('landing.hero_label')}</p>

          <div className="hero-flap-wrapper">
            <SplitFlapText
              words={splitWords}
              padTo={16}
              fontSize={52}
              flipsPerChar={6}
              cycleDelay={2800}
              charset="alpha"
            />
          </div>

          <p className="hero-subtitle">{t('landing.hero_subtitle')}</p>

          <div className="hero-actions">
            <Button to="/registrar-cidadao" variant="primary" size="lg">
              {t('landing.cta_register')}
            </Button>
            <Button to="/consulta" variant="secondary" size="lg">
              {t('landing.cta_lookup')}
            </Button>
          </div>
        </div>
      </main>

      {/* ── Como funciona ─────────────────────────────────────────────── */}
      <section className="landing-section landing-section--alt">
        <div className="section-inner">
          <h2 className="section-title">{t('landing.how_it_works.title')}</h2>
          <div className="steps-grid">
            <div className="step-card">
              <span className="step-number">01</span>
              <h3>{t('landing.how_it_works.step1_title')}</h3>
              <p>{t('landing.how_it_works.step1_desc')}</p>
            </div>
            <div className="step-card">
              <span className="step-number">02</span>
              <h3>{t('landing.how_it_works.step2_title')}</h3>
              <p>{t('landing.how_it_works.step2_desc')}</p>
            </div>
            <div className="step-card">
              <span className="step-number">03</span>
              <h3>{t('landing.how_it_works.step3_title')}</h3>
              <p>{t('landing.how_it_works.step3_desc')}</p>
            </div>
          </div>
        </div>
      </section>

      {/* ── Cards de ação principais ──────────────────────────────────── */}
      <section className="landing-section">
        <div className="section-inner">
          <h2 className="section-title">{t('landing.services.title')}</h2>
          <div className="action-cards-grid">

            <Link to="/registrar-cidadao" className="action-card">
              <div className="action-card-icon">
                <IconDocument />
              </div>
              <h3>{t('landing.services.card_register_title')}</h3>
              <p>{t('landing.services.card_register_desc')}</p>
              <div className="action-card-footer">
                {t('landing.services.card_register_action')} <span aria-hidden="true">→</span>
              </div>
            </Link>

            <Link to="/consulta" className="action-card">
              <div className="action-card-icon">
                <IconSearch />
              </div>
              <h3>{t('landing.services.card_lookup_title')}</h3>
              <p>{t('landing.services.card_lookup_desc')}</p>
              <div className="action-card-footer">
                {t('landing.services.card_lookup_action')} <span aria-hidden="true">→</span>
              </div>
            </Link>

            <Link to="/login" className="action-card">
              <div className="action-card-icon">
                <IconShield />
              </div>
              <h3>{t('landing.services.card_operational_title')}</h3>
              <p>{t('landing.services.card_operational_desc')}</p>
              <div className="action-card-footer">
                {t('landing.services.card_operational_action')} <span aria-hidden="true">→</span>
              </div>
            </Link>

          </div>
        </div>
      </section>

      {/* ── O que pode ser registrado ─────────────────────────────────── */}
      <section className="landing-section landing-section--alt">
        <div className="section-inner">
          <h2 className="section-title">{t('landing.types.title')}</h2>
          <p className="section-subtitle">{t('landing.types.subtitle')}</p>
          <div className="types-grid">
            {[
              { titulo: t('landing.types.item1_title'), desc: t('landing.types.item1_desc') },
              { titulo: t('landing.types.item2_title'), desc: t('landing.types.item2_desc') },
              { titulo: t('landing.types.item3_title'), desc: t('landing.types.item3_desc') },
              { titulo: t('landing.types.item4_title'), desc: t('landing.types.item4_desc') },
              { titulo: t('landing.types.item5_title'), desc: t('landing.types.item5_desc') },
              { titulo: t('landing.types.item6_title'), desc: t('landing.types.item6_desc') },
            ].map(({ titulo, desc }) => (
              <div key={titulo} className="type-card">
                <h4>{titulo}</h4>
                <p>{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Exemplos de registros ─────────────────────────────────────── */}
      <section className="landing-section">
        <div className="section-inner">
          <h2 className="section-title">{t('landing.recent.title')}</h2>
          <p className="section-subtitle">{t('landing.recent.subtitle')}</p>
          <div className="table-wrap">
            <table className="tabela">
              <thead>
                <tr>
                  <th>{t('landing.recent.th_protocol')}</th>
                  <th>{t('landing.recent.th_nature')}</th>
                  <th>{t('landing.recent.th_location')}</th>
                  <th>{t('landing.recent.th_date')}</th>
                  <th>{t('landing.recent.th_status')}</th>
                </tr>
              </thead>
              <tbody>
                {[
                  { proto: 'SGOPI-2026-000140', nat: 'Furto', local: 'Centro, Alegrete/RS', data: '19/09/2026', status: t('status.AGUARDANDO_REVISAO'), cor: 'var(--warn)' },
                  { proto: 'SGOPI-2026-000137', nat: 'Ameaça', local: 'Bairro Piola', data: '19/09/2026', status: t('status.VALIDADA'), cor: 'var(--ok)' },
                  { proto: 'SGOPI-2026-000133', nat: 'Perturbação do Sossego', local: 'Av. Brasil', data: '18/09/2026', status: t('status.EM_ATENDIMENTO'), cor: 'var(--primary)' },
                  { proto: 'SGOPI-2026-000120', nat: 'Dano ao Patrimônio', local: 'Praça da República', data: '18/09/2026', status: t('status.ENCERRADA'), cor: 'var(--muted)' },
                  { proto: 'SGOPI-2026-000115', nat: 'Extravio de Documento', local: 'Bairro São Roque', data: '17/09/2026', status: t('status.VALIDADA'), cor: 'var(--ok)' },
                ].map((row) => (
                  <tr key={row.proto}>
                    <td><code style={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>{row.proto}</code></td>
                    <td>{row.nat}</td>
                    <td>{row.local}</td>
                    <td>{row.data}</td>
                    <td><span style={{ color: row.cor, fontWeight: 600 }}>{row.status}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* ── Consulta integrada ───────────────────────────────────────── */}
      <section className="landing-section landing-section--alt">
        <div className="section-inner" style={{ textAlign: 'center' }}>
          <h2 className="section-title">{t('landing.search.title')}</h2>
          <p className="section-subtitle">{t('landing.search.subtitle')}</p>
          <form
            className="hero-search-form"
            onSubmit={(e) => {
              e.preventDefault();
              const input = (e.currentTarget.elements.namedItem('protocolo') as HTMLInputElement).value.trim().toUpperCase();
              if (input) window.location.href = `/consulta?protocolo=${encodeURIComponent(input)}`;
            }}
          >
            <input
              name="protocolo"
              type="text"
              placeholder={t('landing.search.placeholder')}
              style={{ fontFamily: 'monospace', fontWeight: 600, letterSpacing: '0.04em', textTransform: 'uppercase' }}
              aria-label={t('landing.search.title')}
            />
            <Button type="submit" variant="primary">{t('landing.search.button')}</Button>
          </form>
          <p className="muted small" style={{ marginTop: 12 }}>
            {t('landing.search.hint')}
          </p>
        </div>
      </section>

      {/* ── FAQ ──────────────────────────────────────────────────────── */}
      <section className="landing-section">
        <div className="section-inner">
          <h2 className="section-title">{t('landing.faq.title')}</h2>
          <div className="faq-list">
            {[
              { q: t('landing.faq.q1'), a: t('landing.faq.a1') },
              { q: t('landing.faq.q2'), a: t('landing.faq.a2') },
              { q: t('landing.faq.q3'), a: t('landing.faq.a3') },
              { q: t('landing.faq.q4'), a: t('landing.faq.a4') },
              { q: t('landing.faq.q5'), a: t('landing.faq.a5') },
              { q: t('landing.faq.q6'), a: t('landing.faq.a6') },
            ].map(({ q, a }) => (
              <details key={q} className="faq-item">
                <summary className="faq-question">{q}</summary>
                <p className="faq-answer">{a}</p>
              </details>
            ))}
          </div>
        </div>
      </section>

      {/* ── Footer ───────────────────────────────────────────────────── */}
      <footer className="landing-footer">
        <div className="footer-inner">

          <div className="footer-col">
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
              <LogoSgopi size={22} color="var(--primary)" />
              <strong>{t('app.title').toUpperCase()}</strong>
            </div>
            <p>{t('landing.footer.subtitle')}</p>
            <p>{t('landing.footer.institution')}</p>
            <p className="muted small">{t('landing.footer.course')}</p>
          </div>

          <div className="footer-col">
            <h4>{t('landing.footer.quick_links')}</h4>
            <ul className="footer-links">
              <li><Link to="/">{t('nav.home')}</Link></li>
              <li><Link to="/registrar-cidadao">{t('nav.registrar')}</Link></li>
              <li><Link to="/consulta">{t('nav.lookup')}</Link></li>
              <li><Link to="/login">{t('nav.police_access')}</Link></li>
            </ul>
          </div>

          <div className="footer-col">
            <h4>{t('landing.footer.emergencies')}</h4>
            <ul className="footer-links footer-emergency">
              <li><strong>190</strong> — {t('landing.footer.police')}</li>
              <li><strong>192</strong> — {t('landing.footer.samu')}</li>
              <li><strong>193</strong> — {t('landing.footer.firefighters')}</li>
              <li><strong>156</strong> — {t('landing.footer.civil_defense')}</li>
            </ul>
          </div>

          <div className="footer-col">
            <h4>{t('landing.footer.support')}</h4>
            <address className="footer-address">
              <p>{t('landing.footer.police_dept')}</p>
              <p>{t('landing.footer.address')}</p>
              <p>{t('landing.footer.phone')}</p>
              <p>{t('landing.footer.email')}</p>
              <p className="muted small">{t('landing.footer.hours')}</p>
            </address>
          </div>

        </div>
        <div className="footer-bottom">
          {t('landing.footer.copyright')}
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
