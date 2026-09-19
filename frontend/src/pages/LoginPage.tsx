import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../hooks/useAuth';
import { mensagemDeErro } from '../services/api';
import { rotaInicial } from '../components/RequireRole';
import { LogoSgopi } from '../components/common/LogoSgopi';
import { ThemeToggle } from '../components/common/ThemeToggle';

export const LoginPage: React.FC = () => {
  const { t, i18n } = useTranslation(['auth', 'common']);
  const { entrar } = useAuth();
  const navigate = useNavigate();

  const [login, setLogin] = useState('');
  const [senha, setSenha] = useState('');
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

  const trocarIdioma = (lng: string) => {
    i18n.changeLanguage(lng);
    try {
      localStorage.setItem('sgopi.idioma', lng);
    } catch {
      /* sem persistencia */
    }
  };

  return (
    <div className="login-wrap">
      <Link to="/" className="login-back-link">
        ← Voltar ao Portal Público
      </Link>

      <div className="login-header-controls">
        <select
          aria-label={t('common:idioma')}
          value={i18n.language.slice(0, 2)}
          onChange={(e) => trocarIdioma(e.target.value)}
          style={{ width: 'auto', padding: '4px 8px', fontSize: '0.85rem' }}
        >
          <option value="pt">PT</option>
          <option value="en">EN</option>
        </select>

        <ThemeToggle />
      </div>

      <form className="card login" onSubmit={submit}>
        <div className="login-logo-container">
          <LogoSgopi size={56} color="var(--primary)" />
        </div>

        <h1>{t('common:app.title')}</h1>
        <p className="muted" style={{ marginBottom: 20 }}>
          {t('auth:subtitulo', 'Acesso Restrito às Forças Policiais')}
        </p>

        {erro && <div className="alerta erro" style={{ marginBottom: 16 }}>{erro}</div>}

        <label>
          {t('auth:login')}
          <input
            autoFocus
            autoComplete="username"
            placeholder="Seu usuário"
            value={login}
            onChange={(e) => setLogin(e.target.value)}
          />
        </label>

        <label>
          {t('auth:senha')}
          <input
            type="password"
            autoComplete="current-password"
            placeholder="Sua senha"
            value={senha}
            onChange={(e) => setSenha(e.target.value)}
          />
        </label>

        <button className="btn btn-primary" disabled={ocupado || !login || !senha}>
          {ocupado ? t('common:actions.loading') : 'Entrar no Sistema'}
        </button>

        <div className="demo-presets">
          <div className="demo-presets-title">Atalhos de Demonstração (Seed)</div>
          <div className="demo-presets-buttons">
            <button
              type="button"
              className="btn-preset"
              onClick={() => preencherDemo('agente')}
            >
              <span>Agente</span>
              <span className="small muted">agente</span>
            </button>
            <button
              type="button"
              className="btn-preset"
              onClick={() => preencherDemo('delegado')}
            >
              <span>Delegada</span>
              <span className="small muted">delegado</span>
            </button>
            <button
              type="button"
              className="btn-preset"
              onClick={() => preencherDemo('operador')}
            >
              <span>Operador</span>
              <span className="small muted">operador</span>
            </button>
          </div>
        </div>
      </form>
    </div>
  );
};
