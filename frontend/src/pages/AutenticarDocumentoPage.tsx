import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { StatusBadge } from '../components/StatusBadge';
import { mensagemDeErro } from '../services/api';
import { documentosService } from '../services/documentosService';
import type { DocumentoAutenticado } from '../types/api';

const fmt = (iso: string) => new Date(iso).toLocaleString();

/** Chave do documento fictício criado por `scripts/seed.py` (seed_documento_demo). */
const CHAVE_DEMO = 'SGPX-SENT-DEMX-CHAV-EXEM-PLAR';

/** Portal público de autenticação de documento (RF08 / UC08). Rota sem sessão. */
export const AutenticarDocumentoPage: React.FC = () => {
  const { t } = useTranslation(['publico', 'common', 'ocorrencias']);
  const navigate = useNavigate();
  const { chave: chaveDaRota } = useParams<{ chave?: string }>();
  const [chave, setChave] = useState(chaveDaRota ?? '');
  const [resultado, setResultado] = useState<DocumentoAutenticado | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [ocupado, setOcupado] = useState(false);
  const [copiado, setCopiado] = useState(false);

  const copiarDemo = async () => {
    try {
      await navigator.clipboard.writeText(CHAVE_DEMO);
      setCopiado(true);
      window.setTimeout(() => setCopiado(false), 1800);
    } catch {
      setChave(CHAVE_DEMO);
    }
  };

  const conferir = async (valor: string) => {
    if (!valor.trim()) {
      setErro(t('publico:erro.chave_vazia'));
      return;
    }
    setOcupado(true);
    setErro(null);
    setResultado(null);
    try {
      setResultado(await documentosService.autenticar(valor));
    } catch (err) {
      setErro(mensagemDeErro(err));
    } finally {
      setOcupado(false);
    }
  };

  // QR Code impresso no documento aponta para /autenticar/<chave>: confere ao abrir
  useEffect(() => {
    if (chaveDaRota) void conferir(chaveDaRota);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chaveDaRota]);

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    void conferir(chave);
  };

  const novaConsulta = () => {
    setResultado(null);
    setErro(null);
    setChave('');
    navigate('/autenticar', { replace: true });
  };

  return (
    <div className="login-wrap">
      <Link to="/" className="voltar-inicio">
        <span aria-hidden="true">←</span> {t('publico:voltar_inicio')}
      </Link>
      <div className="card login publico">
        <h1>🛡️ {t('common:app.title')}</h1>
        <h2>{t('publico:titulo')}</h2>
        <p className="muted">{t('publico:subtitulo')}</p>

        {!resultado && (
          <form onSubmit={submit}>
            {erro && <div className="alerta erro" role="alert">{erro}</div>}
            <label>
              {t('publico:chave_label')}
              <input
                autoFocus
                className="chave-input"
                placeholder={t('publico:chave_placeholder')}
                value={chave}
                onChange={(e) => setChave(e.target.value)}
                maxLength={40}
                spellCheck={false}
                autoComplete="off"
              />
            </label>
            <div className="chave-demo">
              <span className="muted small">{t('publico:demo.rotulo')}</span>
              <div className="chave-demo-linha">
                <button type="button" className="chave-demo-valor" onClick={() => setChave(CHAVE_DEMO)} title={t('publico:demo.preencher')}>
                  <code>{CHAVE_DEMO}</code>
                </button>
                <button type="button" className="btn btn-ghost btn-sm" onClick={copiarDemo}>
                  {copiado ? t('publico:demo.copiado') : t('publico:demo.copiar')}
                </button>
              </div>
            </div>
            <button className="btn btn-primary" disabled={ocupado}>
              {ocupado ? t('publico:consultando') : t('publico:consultar')}
            </button>
          </form>
        )}

        {resultado && (
          <div className="resultado-autenticacao" data-situacao={resultado.situacao}>
            <div className={`alerta ${resultado.situacao === 'VALIDO' ? 'sucesso' : 'erro'}`} role="status">
              <strong>{resultado.situacao === 'VALIDO' ? '✔ ' : '⚠ '}{t(`publico:resultado.${resultado.situacao}`)}</strong>
              <div className="small">{t(`publico:resultado.explicacao_${resultado.situacao}`)}</div>
            </div>
            <dl className="grid2">
              <dt>{t('publico:resultado.protocolo')}</dt><dd><strong>{resultado.numero_protocolo}</strong></dd>
              <dt>{t('publico:resultado.status')}</dt><dd><StatusBadge status={resultado.status_ocorrencia} /></dd>
              <dt>{t('publico:resultado.emitido_em')}</dt><dd>{fmt(resultado.emitido_em)}</dd>
              <dt>{t('publico:resultado.consultado_em')}</dt><dd>{fmt(resultado.consultado_em)}</dd>
              <dt>{t('publico:resultado.natureza')}</dt><dd>{resultado.natureza}</dd>
              <dt>{t('publico:resultado.data_fato')}</dt><dd>{fmt(resultado.data_hora_fato)}</dd>
              <dt>{t('publico:resultado.envolvidos')}</dt>
              <dd>
                {Object.entries(resultado.envolvidos_por_tipo).map(([tipo, qtd]) => `${qtd} × ${t(`ocorrencias:envolvido.${tipo}`)}`).join(' · ') || '—'}
              </dd>
              <dt>{t('publico:resultado.evidencias')}</dt><dd>{resultado.quantidade_evidencias}</dd>
            </dl>
            {resultado.tipificacoes.length > 0 && (
              <>
                <h4>{t('publico:resultado.tipificacoes')}</h4>
                <ul className="lista">
                  {resultado.tipificacoes.map((tp, i) => (
                    <li key={i}><span><strong>{tp.artigo}</strong> — {tp.descricao}</span></li>
                  ))}
                </ul>
              </>
            )}
            <p className="muted small hash">{t('publico:resultado.hash')}: <code>{resultado.hash_integridade}</code></p>
            <button type="button" className="btn btn-ghost" onClick={novaConsulta}>{t('publico:resultado.nova_consulta')}</button>
          </div>
        )}

        <p className="muted small">{t('publico:lgpd')}</p>
      </div>
    </div>
  );
};
