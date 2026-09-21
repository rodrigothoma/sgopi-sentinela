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
          <input
            type="password"
            autoComplete="current-password"
            maxLength={100}
            placeholder={t('auth:senha_placeholder')}
            value={senha}
            onChange={(e) => setSenha(e.target.value)}
          />
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

      {/* RF08: atalho para o portal público de autenticação de documento (UC08 regra 1) */}
      <div className="login-divisor" aria-hidden="true"><span>{t('auth:publico.ou')}</span></div>

      <Link to="/autenticar" className="card login-publico">
        <span className="login-publico-icone" aria-hidden="true">🔎</span>
        <span className="login-publico-texto">
          <strong>{t('auth:publico.titulo')}</strong>
          <span className="muted small">{t('auth:publico.subtitulo')}</span>
        </span>
        <span className="login-publico-seta" aria-hidden="true">→</span>
      </Link>
    </div>
  );
};

export default LoginPage;
