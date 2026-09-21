import React, { useEffect, useState } from 'react';
import { Link, useParams, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { NavbarPublica } from '../components/layout/NavbarPublica';
import { ResultadoDocumento } from '../components/publico/ResultadoDocumento';
import { ResultadoProtocolo } from '../components/publico/ResultadoProtocolo';
import { ConsultaPublicaResponse, consultarOcorrenciaPublica, mensagemDeErro } from '../services/api';
import { documentosService } from '../services/documentosService';
import type { DocumentoAutenticado } from '../types/api';
import { ModoConsulta, PLACEHOLDER, detectarModoConsulta, lerEntradaDaUrl } from '../utils/consultaPublica';

/** Ocorrência fictícia já validada criada por `scripts/seed.py` (seed_documento_demo): protocolo e chave do documento. */
const DEMO: Record<ModoConsulta, string> = {
  protocolo: 'SGOPI-2026-000001',
  chave: 'SGPX-SENT-DEMX-CHAV-EXEM-PLAR',
};

const MODOS: ModoConsulta[] = ['protocolo', 'chave'];

type Resultado =
  | { modo: 'protocolo'; dados: ConsultaPublicaResponse }
  | { modo: 'chave'; dados: DocumentoAutenticado };

/**
 * Consulta pública unificada do Portal do Cidadão. Um único campo atende dois
 * identificadores: o protocolo (acompanhamento da ocorrência) e a chave de
 * autenticidade do documento emitido (RF08 / UC08). O modo é inferido pelo
 * formato digitado e pode ser trocado manualmente. Rota sem sessão.
 *
 * Entradas aceitas: `?protocolo=`, `?chave=`, `?codigo=` (detecta) e o
 * deep-link do QR Code `/autenticar/:chave`.
 */
export const ConsultaPublicaPage: React.FC = () => {
  const { t } = useTranslation(['publico', 'common']);
  const [searchParams] = useSearchParams();
  const { chave: chaveDaRota } = useParams<{ chave?: string }>();

  const [modo, setModo] = useState<ModoConsulta>('protocolo');
  const [codigo, setCodigo] = useState('');
  const [modoDetectado, setModoDetectado] = useState(false);
  const [resultado, setResultado] = useState<Resultado | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [ocupado, setOcupado] = useState(false);
  const [copiado, setCopiado] = useState(false);

  const consultar = async (valor: string, modoConsulta: ModoConsulta) => {
    const limpo = valor.trim();
    if (!limpo) {
      setErro(t(`publico:publica.${modoConsulta}.vazio`));
      return;
    }
    setOcupado(true);
    setErro(null);
    setResultado(null);
    try {
      if (modoConsulta === 'protocolo') {
        setResultado({ modo: 'protocolo', dados: await consultarOcorrenciaPublica(limpo.toUpperCase()) });
      } else {
        setResultado({ modo: 'chave', dados: await documentosService.autenticar(limpo) });
      }
    } catch (err) {
      setErro(mensagemDeErro(err, t(`publico:publica.${modoConsulta}.nao_encontrado`)));
    } finally {
      setOcupado(false);
    }
  };

  // Entrada por URL: QR Code (/autenticar/<chave>), link do comprovante (?protocolo=) ou busca da home (?codigo=).
  useEffect(() => {
    const entrada = lerEntradaDaUrl(chaveDaRota, searchParams);
    if (entrada) {
      setModo(entrada.modo);
      setCodigo(entrada.valor);
      void consultar(entrada.valor, entrada.modo);
      return;
    }
    const modoUrl = searchParams.get('modo');
    if (modoUrl === 'chave' || modoUrl === 'protocolo') setModo(modoUrl);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chaveDaRota, searchParams]);

  const aoDigitar = (valor: string) => {
    const maiusculo = valor.toUpperCase();
    setCodigo(maiusculo);
    const inferido = detectarModoConsulta(maiusculo);
    if (inferido && inferido !== modo) {
      setModo(inferido);
      setModoDetectado(true);
    }
  };

  const trocarModo = (novo: ModoConsulta) => {
    setModo(novo);
    setModoDetectado(false);
    setErro(null);
    setResultado(null);
  };

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    void consultar(codigo, modo);
  };

  const usarDemo = () => {
    setCodigo(DEMO[modo]);
    setModoDetectado(false);
  };

  const copiarDemo = async () => {
    try {
      await navigator.clipboard.writeText(DEMO[modo]);
      setCopiado(true);
      window.setTimeout(() => setCopiado(false), 1800);
    } catch {
      usarDemo();
    }
  };

  return (
    <div className="portal-wrap">
      <NavbarPublica />

      <main className="pagina" style={{ maxWidth: 760, padding: '40px 20px' }}>
        <div className="card consulta-publica" style={{ padding: '32px' }}>
          <h2>{t('publico:publica.titulo')}</h2>
          <p className="muted">{t('publico:publica.subtitulo')}</p>

          <div className="tabs modo-consulta" role="tablist" aria-label={t('publico:publica.modo_rotulo')}>
            {MODOS.map((m) => (
              <button
                key={m}
                type="button"
                role="tab"
                aria-selected={modo === m}
                className={`tab ${modo === m ? 'ativo' : ''}`}
                onClick={() => trocarModo(m)}
              >
                {t(`publico:publica.${m}.aba`)}
              </button>
            ))}
          </div>

          <form onSubmit={submit}>
            <label htmlFor="codigo-consulta">{t(`publico:publica.${modo}.rotulo`)}</label>
            <div className="consulta-publica-linha">
              <input
                id="codigo-consulta"
                className="chave-input"
                placeholder={PLACEHOLDER[modo]}
                value={codigo}
                onChange={(e) => aoDigitar(e.target.value)}
                maxLength={40}
                spellCheck={false}
                autoComplete="off"
                autoFocus
              />
              <button type="submit" className="btn btn-primary" disabled={ocupado || !codigo.trim()}>
                {ocupado ? t('common:actions.loading') : t(`publico:publica.${modo}.botao`)}
              </button>
            </div>
            <p className="muted small consulta-publica-ajuda">
              {modoDetectado
                ? t(`publico:publica.${modo}.detectado`)
                : t(`publico:publica.${modo}.ajuda`)}
            </p>

            <div className="codigo-demo">
              <span className="muted small">{t(`publico:publica.${modo}.demo_rotulo`)}</span>
              <div className="codigo-demo-linha">
                <button type="button" className="codigo-demo-valor" onClick={usarDemo} title={t('publico:demo.preencher')}>
                  <code>{DEMO[modo]}</code>
                </button>
                <button type="button" className="btn btn-ghost btn-sm" onClick={copiarDemo}>
                  {copiado ? t('publico:demo.copiado') : t('publico:demo.copiar')}
                </button>
              </div>
            </div>
          </form>

          {erro && <div className="alerta erro" role="alert" style={{ marginTop: 20 }}>{erro}</div>}

          {resultado && (
            <div className="consulta-publica-resultado">
              {resultado.modo === 'protocolo'
                ? <ResultadoProtocolo dados={resultado.dados} />
                : <ResultadoDocumento dados={resultado.dados} />}

              <div style={{ marginTop: 20, textAlign: 'right' }}>
                <Link to="/" className="btn btn-ghost">
                  {t('publico:consulta.detalhes.voltar_inicio')}
                </Link>
              </div>
            </div>
          )}

          <p className="muted small" style={{ marginTop: 24 }}>{t('publico:lgpd')}</p>
        </div>
      </main>
    </div>
  );
};

export default ConsultaPublicaPage;
