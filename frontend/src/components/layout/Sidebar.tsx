import React, { useEffect, useState } from 'react';
import { NavLink, Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../hooks/useAuth';
import { LogoSgopi } from '../common/LogoSgopi';
import { ThemeToggle } from '../common/ThemeToggle';
import { GlideSelect, GlideSelectOption } from '../common/GlideSelect';
import { trocarIdiomaGlobal } from '../../i18n';
import './Sidebar.css';

/* ─── Ícones Táticos SVG (Vetor inline, nítido e responsivo) ──────────── */

const IconDashboard = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="3" width="7" height="9" rx="1.5" />
    <rect x="14" y="3" width="7" height="5" rx="1.5" />
    <rect x="14" y="12" width="7" height="9" rx="1.5" />
    <rect x="3" y="16" width="7" height="5" rx="1.5" />
  </svg>
);

const IconRegistrar = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline points="14 2 14 8 20 8" />
    <line x1="12" y1="18" x2="12" y2="12" />
    <line x1="9" y1="15" x2="15" y2="15" />
  </svg>
);

const IconMinhas = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round">
    <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
    <line x1="9" y1="14" x2="15" y2="14" />
  </svg>
);

const IconFila = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round">
    <path d="M9 11l3 3L22 4" />
    <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
  </svg>
);

const IconInqueritos = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round">
    <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
    <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
    <line x1="9" y1="7" x2="15" y2="7" />
    <line x1="9" y1="11" x2="13" y2="11" />
  </svg>
);

const IconLaudos = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round">
    <path d="M6 18h8" />
    <path d="M3 22h18" />
    <path d="M14 22a7 7 0 1 0 0-14h-1" />
    <path d="M9 14h2" />
    <path d="M9 12a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2" />
  </svg>
);

const IconMedidas = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    <path d="M12 8v4" />
    <circle cx="12" cy="16" r="0.8" fill="currentColor" />
  </svg>
);

const IconPainel = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10" />
    <line x1="22" y1="12" x2="18" y2="12" />
    <line x1="6" y1="12" x2="2" y2="12" />
    <line x1="12" y1="6" x2="12" y2="2" />
    <line x1="12" y1="22" x2="12" y2="18" />
    <circle cx="12" cy="12" r="3" />
  </svg>
);

const IconFrota = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round">
    <rect x="2" y="4" width="14" height="11" rx="2" />
    <polygon points="16 7 19 7 22 10 22 15 16 15 16 7" />
    <circle cx="6" cy="18" r="2" />
    <circle cx="17" cy="18" r="2" />
  </svg>
);

const IconAuditoria = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10" />
    <polyline points="12 6 12 12 15 15" />
  </svg>
);

const IconChevronLeft = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="15 18 9 12 15 6" />
  </svg>
);

const IconChevronRight = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="9 18 15 12 9 6" />
  </svg>
);

const IconLogout = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
    <polyline points="16 17 21 12 16 7" />
    <line x1="21" y1="12" x2="9" y2="12" />
  </svg>
);

/* ─── Opções de Idioma ─────────────────────────────────────────────────── */

const OPCOES_IDIOMA: GlideSelectOption[] = [
  { value: 'pt', label: 'PT', tag: 'Português' },
  { value: 'en', label: 'EN', tag: 'English' },
];

const CHAVE_STORAGE = 'sgopi.sidebar_colapsada';
// Mesmo limite do @media em Sidebar.css: abaixo dele a sidebar vira menu deslizante (drawer).
const CONSULTA_MOBILE = '(max-width: 900px)';

/** No celular o menu é sempre completo: o estado "recolhida" salvo no desktop não se aplica. */
function useTelaMobile(): boolean {
  const [mobile, setMobile] = useState(() => window.matchMedia(CONSULTA_MOBILE).matches);
  useEffect(() => {
    const consulta = window.matchMedia(CONSULTA_MOBILE);
    const atualizar = () => setMobile(consulta.matches);
    consulta.addEventListener('change', atualizar);
    return () => consulta.removeEventListener('change', atualizar);
  }, []);
  return mobile;
}

interface SidebarProps {
  mobileAberta?: boolean;
  onFecharMobile?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ mobileAberta = false, onFecharMobile }) => {
  const { t, i18n } = useTranslation('common');
  const { usuario, sair, tem } = useAuth();
  const navigate = useNavigate();

  const telaMobile = useTelaMobile();
  const [preferenciaColapsada, setPreferenciaColapsada] = useState<boolean>(() => {
    try {
      return localStorage.getItem(CHAVE_STORAGE) === 'true';
    } catch {
      return false;
    }
  });

  const colapsada = preferenciaColapsada && !telaMobile;

  const toggleColapso = () => {
    setPreferenciaColapsada((atual) => {
      const proximo = !atual;
      try {
        localStorage.setItem(CHAVE_STORAGE, String(proximo));
      } catch {
        /* sem localStorage */
      }
      return proximo;
    });
  };

  const idiomaAtual = i18n.language ? i18n.language.slice(0, 2) : 'pt';
  const proximoIdioma = idiomaAtual === 'pt' ? 'en' : 'pt';

  const itensNav = [
    { to: '/inicio', label: t('nav.inicio'), icon: <IconDashboard />, visivel: true },
    { to: '/registrar', label: t('nav.registrar'), icon: <IconRegistrar />, visivel: tem('AGENTE') },
    { to: '/minhas', label: t('nav.minhas'), icon: <IconMinhas />, visivel: tem('AGENTE') },
    { to: '/fila', label: t('nav.fila'), icon: <IconFila />, visivel: tem('DELEGADO', 'SUPERVISOR') },
    { to: '/inqueritos', label: t('nav.inqueritos'), icon: <IconInqueritos />, visivel: tem('DELEGADO', 'SUPERVISOR') },
    { to: '/laudos', label: t('nav.laudos'), icon: <IconLaudos />, visivel: tem('DELEGADO', 'PERITO', 'SUPERVISOR') },
    { to: '/medidas', label: t('nav.medidas'), icon: <IconMedidas />, visivel: tem('DELEGADO', 'SUPERVISOR', 'AGENTE') },
    { to: '/painel', label: t('nav.painel'), icon: <IconPainel />, visivel: tem('OPERADOR_CENTRAL', 'SUPERVISOR', 'DELEGADO') },
    { to: '/frota', label: t('nav.frota'), icon: <IconFrota />, visivel: tem('OPERADOR_CENTRAL', 'SUPERVISOR') },
    { to: '/auditoria', label: t('nav.auditoria'), icon: <IconAuditoria />, visivel: tem('DELEGADO', 'SUPERVISOR') },
  ];

  const handleLinkClick = () => {
    if (onFecharMobile) onFecharMobile();
  };

  const inicialNome = usuario?.nome ? usuario.nome.charAt(0).toUpperCase() : 'U';

  return (
    <>
      {mobileAberta && <div className="sidebar-backdrop" onClick={onFecharMobile} />}
      <aside className={`sidebar ${colapsada ? 'colapsada' : ''} ${mobileAberta ? 'mobile-aberta' : ''}`}>
        {/* Topo: Logo & Botão de Recolher/Expandir */}
        <div className="sidebar-header">
          <Link to="/" className="sidebar-brand-link" title={t('sidebar.voltar_portal')} onClick={handleLinkClick}>
            <LogoSgopi size={colapsada ? 26 : 28} color="var(--primary)" />
            {!colapsada && <span className="sidebar-brand-text">{t('app.title')}</span>}
          </Link>
          <button
            type="button"
            className="sidebar-toggle-btn"
            onClick={toggleColapso}
            title={colapsada ? t('sidebar.expandir') : t('sidebar.recolher')}
            aria-label={colapsada ? t('sidebar.expandir') : t('sidebar.recolher')}
          >
            {colapsada ? <IconChevronRight /> : <IconChevronLeft />}
          </button>
        </div>

        {/* Navegação Central: Lista de Módulos (com nav e a para compatibilidade E2E) */}
        <nav className="sidebar-nav">
          {itensNav.filter((item) => item.visivel).map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
              title={colapsada ? item.label : undefined}
              onClick={handleLinkClick}
            >
              <span className="sidebar-icon">{item.icon}</span>
              {!colapsada && <span className="sidebar-label">{item.label}</span>}
            </NavLink>
          ))}
        </nav>

        {/* Rodapé: Perfil, Utilitários de Idioma/Tema e Logout */}
        <div className="sidebar-footer">
          {usuario && (
            <div className="sidebar-user-card" title={`${usuario.nome} (${t(`papel.${usuario.papel}`)})`}>
              <div className="sidebar-user-avatar">{inicialNome}</div>
              {!colapsada && (
                <div className="sidebar-user-info">
                  <span className="sidebar-user-name">{usuario.nome}</span>
                  <span className="sidebar-user-role">{t(`papel.${usuario.papel}`)}</span>
                </div>
              )}
            </div>
          )}

          {/* Controles de Idioma e Tema */}
          <div className="sidebar-controls">
            {!colapsada ? (
              <>
                <GlideSelect
                  options={OPCOES_IDIOMA}
                  value={idiomaAtual}
                  onChange={(val) => trocarIdiomaGlobal(val)}
                  size="sm"
                  menuWidth={130}
                  showTags
                  ariaLabel={t('idioma')}
                />
                <ThemeToggle />
              </>
            ) : (
              <>
                <button
                  type="button"
                  className="sidebar-lang-toggle"
                  onClick={() => trocarIdiomaGlobal(proximoIdioma)}
                  title={t('sidebar.alternar_idioma', { idioma: idiomaAtual.toUpperCase() })}
                >
                  {idiomaAtual.toUpperCase()}
                </button>
                <ThemeToggle />
              </>
            )}
          </div>

          {/* Botão Sair */}
          <button
            type="button"
            className="sidebar-logout-btn"
            title={t('actions.sair')}
            onClick={() => {
              sair();
              navigate('/login');
            }}
          >
            <IconLogout />
            {!colapsada && <span>{t('actions.sair')}</span>}
          </button>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
