import React, { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { NavbarPublica } from '../components/layout/NavbarPublica';
import { ConsultaPublicaResponse, consultarOcorrenciaPublica, mensagemDeErro } from '../services/api';

const STATUS_ETAPAS = [
  { id: 'AGUARDANDO_REVISAO', rotulo: 'Triagem Policial' },
  { id: 'VALIDADA', rotulo: 'Validada' },
  { id: 'EM_ATENDIMENTO', rotulo: 'Em Atendimento' },
  { id: 'ENCERRADA', rotulo: 'Finalizada' }
];

export const ConsultaProtocoloPage: React.FC = () => {
  const { t } = useTranslation('common');
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
      setErro(mensagemDeErro(err, 'Ocorrência não encontrada com o protocolo informado. Verifique os dígitos e tente novamente.'));
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

  return (
    <div className="portal-wrap">
      <NavbarPublica />

      <main className="pagina" style={{ maxWidth: 760, padding: '40px 20px' }}>
        <div className="card" style={{ padding: '32px' }}>
          <h2>Consulta Pública de Ocorrência</h2>
          <p className="muted">
            Digite o número de protocolo oficial (ex: <code>SGOPI-2026-000001</code>) para consultar
            o status e a tramitação do seu atendimento policial.
          </p>

          <form onSubmit={handleSubmit} style={{ display: 'flex', gap: 10, marginTop: 20 }}>
            <input
              type="text"
              placeholder="SGOPI-AAAA-NNNNNN"
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
              {ocupado ? t('actions.loading') : 'Consultar'}
            </button>
          </form>

          {erro && <div className="alerta erro" style={{ marginTop: 20 }}>{erro}</div>}

          {resultado && (
            <div style={{ marginTop: 32, borderTop: '1px solid var(--line)', paddingTop: 24 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
                <div>
                  <span className="small muted">PROTOCOLO:</span>
                  <div style={{ fontSize: '1.3rem', fontWeight: 700, color: 'var(--primary)' }}>
                    {resultado.numero_protocolo}
                  </div>
                </div>
                <div className="pill" style={{ fontSize: '0.85rem' }}>
                  {t(`status.${resultado.status}`, resultado.status)}
                </div>
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
                      <div className="timeline-dot">
                        {isCompleted ? '✓' : idx + 1}
                      </div>
                      <div className="timeline-label">{etapa.rotulo}</div>
                    </div>
                  );
                })}
              </div>

              <dl className="grid2" style={{ marginTop: 24 }}>
                <dt>Natureza:</dt>
                <dd><strong>{resultado.natureza}</strong></dd>

                <dt>Local do Fato:</dt>
                <dd>{resultado.localizacao}</dd>

                <dt>Data de Abertura:</dt>
                <dd>{new Date(resultado.criada_em).toLocaleString('pt-BR')}</dd>

                {resultado.desfecho && (
                  <>
                    <dt>Desfecho Policial:</dt>
                    <dd>{resultado.desfecho}</dd>
                  </>
                )}
              </dl>

              <div style={{ marginTop: 20, textAlign: 'right' }}>
                <Link to="/" className="btn btn-ghost">
                  Voltar à Página Inicial
                </Link>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};
