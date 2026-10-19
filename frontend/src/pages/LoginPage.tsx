import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../hooks/useAuth';
import { mensagemDeErro } from '../services/api';
import { rotaInicial } from '../components/RequireRole';
import { LogoSgopi } from '../components/common/LogoSgopi';
import { ThemeToggle } from '../components/common/ThemeToggle';
import { GlideSelect, GlideSelectOption } from '../components/common/GlideSelect';
import { Button } from '../components/common/Button';
import { trocarIdiomaGlobal } from '../i18n';

const OPCOES_IDIOMA: GlideSelectOption[] = [
  { value: 'pt', label: 'PT', tag: 'Português' },
  { value: 'en', label: 'EN', tag: 'English' },
];

/* Ícones inline do alternador de visibilidade — mesmo traço dos demais ícones do app. */
const IconeOlho = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
    <circle cx="12" cy="12" r="3" />
  </svg>
);

const IconeOlhoFechado = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />
    <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19" />
    <path d="M14.12 14.12a3 3 0 1 1-4.24-4.24" />
    <line x1="1" y1="1" x2="23" y2="23" />
  </svg>
);

export const LoginPage: React.FC = () => {
  const { t, i18n } = useTranslation(['auth', 'common']);
  const { entrar } = useAuth();
  const navigate = useNavigate();

  const [login, setLogin] = useState('');
  const [senha, setSenha] = useState('');
  const [senhaVisivel, setSenhaVisivel] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [ocupado, setOcupado] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setOcupado(true);
    setErro(null);
    try {
      const u = await entrar(login, senha);
      navigate(rotaInicial(u.papel), { replace: true });
    } catch (err) {
      setErro(mensagemDeErro(err, t('auth:erro_generico')));
    } finally {
      setOcupado(false);
    }
  };

  const preencherDemo = (user: string) => {
    setLogin(user);
    setSenha('Senha@123');
    setErro(null);
  };

  const idiomaAtual = i18n.language ? i18n.language.slice(0, 2) : 'pt';

  return (
    <div className="login-wrap">
      <Link to="/" className="login-back-link">
        {t('auth:voltar_portal')}
      </Link>

      <div className="login-header-controls">
        <GlideSelect
          options={OPCOES_IDIOMA}
          value={idiomaAtual}
          onChange={(val) => trocarIdiomaGlobal(val)}
          size="sm"
          menuWidth={140}
          showTags
          ariaLabel={t('common:idioma')}
        />

        <ThemeToggle />
      </div>

      <form className="card login" onSubmit={submit}>
        <div className="login-logo-container">
          <LogoSgopi size={56} color="var(--primary)" />
        </div>

        <h1>{t('common:app.title')}</h1>
        <p className="muted" style={{ marginBottom: 20 }}>
          {t('auth:subtitulo')}
        </p>

        {erro && <div className="alerta erro" style={{ marginBottom: 16 }}>{erro}</div>}

        <label>
          {t('auth:login')}
          <input
            autoFocus
            autoComplete="username"
            maxLength={50}
            placeholder={t('auth:login_placeholder')}
            value={login}
            onChange={(e) => setLogin(e.target.value)}
          />
        </label>

        <label>
          {t('auth:senha')}
          <span className="campo-senha">
            <input
              type={senhaVisivel ? 'text' : 'password'}
              autoComplete="current-password"
              maxLength={100}
              placeholder={t('auth:senha_placeholder')}
              value={senha}
              onChange={(e) => setSenha(e.target.value)}
            />
            <button
              type="button"
              className="campo-senha-olho"
              onClick={() => setSenhaVisivel((v) => !v)}
              aria-label={t(senhaVisivel ? 'auth:senha_ocultar' : 'auth:senha_mostrar')}
              aria-pressed={senhaVisivel}
              title={t(senhaVisivel ? 'auth:senha_ocultar' : 'auth:senha_mostrar')}
              tabIndex={-1}
            >
              {senhaVisivel ? <IconeOlhoFechado /> : <IconeOlho />}
            </button>
          </span>
        </label>

        <Button
          type="submit"
          variant="primary"
          size="md"
          fullWidth
          loading={ocupado}
          disabled={!login || !senha}
          style={{ marginTop: 20 }}
        >
          {ocupado ? t('common:actions.loading') : t('auth:entrar')}
        </Button>

        <div className="demo-presets">
          <div className="demo-presets-title">{t('auth:demo_titulo')}</div>
          <div className="demo-presets-buttons">
            <button
              type="button"
              className="btn-preset"
              onClick={() => preencherDemo('agente')}
            >
              <span>{t('auth:perfis.agente')}</span>
              <span className="small muted">agente</span>
            </button>
            <button
              type="button"
              className="btn-preset"
              onClick={() => preencherDemo('delegado')}
            >
              <span>{t('auth:perfis.delegado')}</span>
              <span className="small muted">delegado</span>
            </button>
            <button
              type="button"
              className="btn-preset"
              onClick={() => preencherDemo('operador')}
            >
              <span>{t('auth:perfis.operador')}</span>
              <span className="small muted">operador</span>
            </button>
          </div>
        </div>
      </form>
    </div>
  );
};

export default LoginPage;
