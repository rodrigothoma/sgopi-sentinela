import React from 'react';
import { useTheme } from '../../hooks/useTheme';
import './ThemeToggle.css';

/* ─── SVGs inline — sol (light) e lua (dark) ─────────────────────────────── */

const IconSun: React.FC = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 20 20"
    width="14"
    height="14"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.6"
    strokeLinecap="round"
    aria-hidden="true"
  >
    {/* centro */}
    <circle cx="10" cy="10" r="3.5" />
    {/* raios */}
    <line x1="10" y1="1.5"  x2="10" y2="3.5"  />
    <line x1="10" y1="16.5" x2="10" y2="18.5" />
    <line x1="1.5"  y1="10" x2="3.5"  y2="10" />
    <line x1="16.5" y1="10" x2="18.5" y2="10" />
    <line x1="4.1"  y1="4.1"  x2="5.5"  y2="5.5"  />
    <line x1="14.5" y1="14.5" x2="15.9" y2="15.9" />
    <line x1="15.9" y1="4.1"  x2="14.5" y2="5.5"  />
    <line x1="5.5"  y1="14.5" x2="4.1"  y2="15.9" />
  </svg>
);

const IconMoon: React.FC = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 20 20"
    width="14"
    height="14"
    fill="currentColor"
    aria-hidden="true"
  >
    {/* crescente — caminho clássico de meia-lua */}
    <path d="M15.5 13.4A7 7 0 0 1 6.6 4.5a7 7 0 1 0 8.9 8.9z" />
  </svg>
);

/* ─── Componente ──────────────────────────────────────────────────────────── */

interface ThemeToggleProps {
  /** Se true, exibe o label "Claro" / "Escuro" ao lado do toggle */
  showLabel?: boolean;
  className?: string;
}

export const ThemeToggle: React.FC<ThemeToggleProps> = ({
  showLabel = false,
  className = '',
}) => {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === 'dark';

  return (
    <button
      type="button"
      role="switch"
      aria-checked={isDark}
      aria-label={isDark ? 'Alternar para tema claro' : 'Alternar para tema escuro'}
      onClick={toggleTheme}
      className={`theme-toggle ${isDark ? 'theme-toggle--dark' : 'theme-toggle--light'} ${className}`.trim()}
      title={isDark ? 'Tema escuro ativado — clique para claro' : 'Tema claro ativado — clique para escuro'}
    >
      {/* trilho da pílula */}
      <span className="theme-toggle__track" aria-hidden="true">
        {/* ícone fixo de sol (lado esquerdo do trilho) */}
        <span className="theme-toggle__track-icon theme-toggle__track-icon--sun">
          <IconSun />
        </span>
        {/* ícone fixo de lua (lado direito do trilho) */}
        <span className="theme-toggle__track-icon theme-toggle__track-icon--moon">
          <IconMoon />
        </span>
        {/* polegar deslizante com o ícone ativo dentro */}
        <span className="theme-toggle__thumb">
          {isDark ? <IconMoon /> : <IconSun />}
        </span>
      </span>

      {showLabel && (
        <span className="theme-toggle__label">
          {isDark ? 'Escuro' : 'Claro'}
        </span>
      )}
    </button>
  );
};

export default ThemeToggle;
