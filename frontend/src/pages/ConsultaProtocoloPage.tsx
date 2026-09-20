import React, { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { NavbarPublica } from '../components/layout/NavbarPublica';
import { StatusBadge } from '../components/StatusBadge';
import { ConsultaPublicaResponse, consultarOcorrenciaPublica, mensagemDeErro } from '../services/api';

const STATUS_ETAPAS = [
  { id: 'AGUARDANDO_REVISAO', rotuloChave: 'triagem' },
  { id: 'VALIDADA', rotuloChave: 'validada' },
  { id: 'EM_ATENDIMENTO', rotuloChave: 'atendimento' },
  { id: 'ENCERRADA', rotuloChave: 'finalizada' },
];

export const ConsultaProtocoloPage: React.FC = () => {
  const { t, i18n } = useTranslation(['publico', 'common']);
  const [searchParams] = useSearchParams();
  const [protocoloInput, setProtocoloInput] = useState(searchParams.get('protocolo') ?? '');
  const [resultado, setResultado] = useState<ConsultaPublicaResponse | null>(null);
  const [ocupado, setOcupado] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  const consultar = async (p: string) => {
    const limpo = p.trim();
    if (!limpo) return;
    setOcupado(true);
    setErro(null);
    try {
      const dados = await consultarOcorrenciaPublica(limpo);
      setResultado(dados);
    } catch (err) {
      setResultado(null);
      setErro(mensagemDeErro(err, t('publico:consulta.erro_nao_encontrada')));
    } finally {
      setOcupado(false);
    }
  };

  useEffect(() => {
    const p = searchParams.get('protocolo');
    if (p) {
      consultar(p);
    }
  }, [searchParams]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    consultar(protocoloInput);
  };

  const getEtapaIndex = (status: string) => {
    if (status === 'AGUARDANDO_REVISAO' || status === 'EM_CORRECAO') return 0;
    if (status === 'VALIDADA' || status === 'EM_DESPACHO') return 1;
    if (status === 'EM_ATENDIMENTO') return 2;
    if (status === 'ENCERRADA' || status === 'REJEITADA') return 3;
    return 0;
  };

  const localeData = i18n.language && i18n.language.startsWith('en') ? 'en-US' : 'pt-BR';

  return (
    <div className="portal-wrap">
      <NavbarPublica />

      <main className="pagina" style={{ maxWidth: 760, padding: '40px 20px' }}>
        <div className="card" style={{ padding: '32px' }}>
          <h2>{t('publico:consulta.titulo')}</h2>
          <p className="muted">{t('publico:consulta.subtitulo')}</p>

          <form onSubmit={handleSubmit} style={{ display: 'flex', gap: 10, marginTop: 20 }}>
            <input
              type="text"
              placeholder={t('publico:consulta.placeholder')}
              value={protocoloInput}
              onChange={(e) => setProtocoloInput(e.target.value.toUpperCase())}
              style={{ fontSize: '1.05rem', fontWeight: 600, letterSpacing: '0.04em' }}
            />
            <button
              type="submit"
              className="btn btn-primary"
              disabled={ocupado || !protocoloInput.trim()}
              style={{ padding: '0 24px' }}
            >
              {ocupado ? t('common:actions.loading') : t('publico:consulta.botao_consultar')}
            </button>
          </form>

          {erro && <div className="alerta erro" style={{ marginTop: 20 }}>{erro}</div>}

          {resultado && (
            <div style={{ marginTop: 32, borderTop: '1px solid var(--line)', paddingTop: 24 }}>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: 12,
                }}
              >
                <div>
                  <span className="small muted">{t('publico:consulta.protocolo_rotulo')}</span>
                  <div style={{ fontSize: '1.3rem', fontWeight: 700, color: 'var(--primary)' }}>
                    {resultado.numero_protocolo}
                  </div>
                </div>
                <StatusBadge status={resultado.status} />
              </div>

              <div className="status-timeline">
                {STATUS_ETAPAS.map((etapa, idx) => {
                  const atualIdx = getEtapaIndex(resultado.status);
                  const isCompleted = idx < atualIdx;
                  const isActive = idx === atualIdx;

                  return (
                    <div
                      key={etapa.id}
                      className={`timeline-step ${isActive ? 'active' : ''} ${isCompleted ? 'completed' : ''}`}
                    >
                      <div className="timeline-dot">{isCompleted ? '✓' : idx + 1}</div>
                      <div className="timeline-label">
                        {t(`publico:consulta.etapas.${etapa.rotuloChave}`)}
                      </div>
                    </div>
                  );
                })}
              </div>

              <dl className="grid2" style={{ marginTop: 24 }}>
                <dt>{t('publico:consulta.detalhes.natureza')}</dt>
                <dd>
                  <strong>{resultado.natureza}</strong>
                </dd>

                <dt>{t('publico:consulta.detalhes.local')}</dt>
                <dd>{resultado.localizacao}</dd>

                <dt>{t('publico:consulta.detalhes.data_abertura')}</dt>
                <dd>{new Date(resultado.criada_em).toLocaleString(localeData)}</dd>

                {resultado.desfecho && (
                  <>
                    <dt>{t('publico:consulta.detalhes.desfecho')}</dt>
                    <dd>{resultado.desfecho}</dd>
                  </>
                )}
              </dl>

              <div style={{ marginTop: 20, textAlign: 'right' }}>
                <Link to="/" className="btn btn-ghost">
                  {t('publico:consulta.detalhes.voltar_inicio')}
                </Link>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default ConsultaProtocoloPage;
