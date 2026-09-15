import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { mensagemDeErro } from '../services/api';
import { rotaInicial } from '../components/RequireRole';

export const LoginPage: React.FC = () => {
  const { t } = useTranslation(['auth', 'common']);
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

  return (
    <div className="login-wrap">
      <div className="login-coluna">
        <form className="card login" onSubmit={submit}>
          <h1>🛡️ {t('common:app.title')}</h1>
          <p className="muted">{t('auth:subtitulo')}</p>
          {erro && <div className="alerta erro">{erro}</div>}
          <label>
            {t('auth:login')}
            <input autoFocus autoComplete="username" value={login} onChange={(e) => setLogin(e.target.value)} />
          </label>
          <label>
            {t('auth:senha')}
            <input type="password" autoComplete="current-password" value={senha} onChange={(e) => setSenha(e.target.value)} />
          </label>
          <button className="btn btn-primary" disabled={ocupado || !login || !senha}>
            {ocupado ? t('common:actions.loading') : t('auth:entrar')}
          </button>
          <p className="muted small">{t('auth:dica_seed')}</p>
        </form>

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
    </div>
  );
};
