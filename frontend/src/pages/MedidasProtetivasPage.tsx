import React, { useCallback, useEffect, useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../hooks/useToast';
import { mensagemDeErro } from '../services/api';
import { medidasService, type MedidaProtetiva } from '../services/medidasService';

const TIPOS_RESTRICAO_OPCOES = [
  { id: 'AFASTAMENTO_DO_LAR', label: 'Afastamento do Lar / Domicílio' },
  { id: 'PROIBICAO_DE_CONTATO', label: 'Proibição de Contato por Qualquer Meio' },
  { id: 'LIMITE_DISTANCIA_METROS', label: 'Limite Mínimo de Distância (Metros)' },
  { id: 'SUSPENSAO_PORTE_ARMAS', label: 'Suspensão da Posse ou Porte de Armas' },
  { id: 'OUTRA', label: 'Outras Restrições Judiciais / Cautelares' },
];

export const MedidasProtetivasPage: React.FC = () => {
  const { tem } = useAuth();
  const { avisar } = useToast();

  const [medidas, setMedidas] = useState<MedidaProtetiva[]>([]);
  const [total, setTotal] = useState(0);
  const [carregando, setCarregando] = useState(false);

  // Filtros
  const [filtroStatus, setFiltroStatus] = useState<string>('TODOS');

  // Modais
  const [modalConcederAberto, setModalConcederAberto] = useState(false);
  const [modalRenovarAberto, setModalRenovarAberto] = useState(false);
  const [modalRevogarAberto, setModalRevogarAberto] = useState(false);
  const [medidaAlvo, setMedidaAlvo] = useState<MedidaProtetiva | null>(null);

  // Form Conceder
  const [ocorrenciaId, setOcorrenciaId] = useState('');
  const [vitimaId, setVitimaId] = useState('');
  const [agressorId, setAgressorId] = useState('');
  const [restricoesSelecionadas, setRestricoesSelecionadas] = useState<string[]>([
    'AFASTAMENTO_DO_LAR',
    'PROIBICAO_DE_CONTATO',
  ]);
  const [prazoDias, setPrazoDias] = useState<number>(90);
  const [distanciaMinima, setDistanciaMinima] = useState<number>(300);
  const [condicoesEspecificas, setCondicoesEspecificas] = useState('');

  // Form Renovar
  const [diasAdicionais, setDiasAdicionais] = useState<number>(30);
  const [justificativaRenovacao, setJustificativaRenovacao] = useState('');

  // Form Revogar
  const [motivoRevogacao, setMotivoRevogacao] = useState('');

  const carregarMedidas = useCallback(async () => {
    setCarregando(true);
    try {
      const statusParam = filtroStatus === 'TODOS' ? undefined : [filtroStatus];
      const res = await medidasService.listar({ status: statusParam });
      setMedidas(res.itens);
      setTotal(res.total);
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    } finally {
      setCarregando(false);
    }
  }, [filtroStatus, avisar]);

  useEffect(() => {
    carregarMedidas();
  }, [carregarMedidas]);

  const executarConcessao = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ocorrenciaId.trim() || !vitimaId.trim() || !agressorId.trim()) {
      avisar('Preencha os IDs da ocorrência, vítima e agressor.', 'erro');
      return;
    }
    if (vitimaId.trim() === agressorId.trim()) {
      avisar('Vítima e agressor não podem ser a mesma pessoa.', 'erro');
      return;
    }
    if (restricoesSelecionadas.length === 0) {
      avisar('Selecione ao menos um tipo de restrição cautelar.', 'erro');
      return;
    }
    try {
      const nova = await medidasService.conceder({
        ocorrencia_id: ocorrenciaId.trim(),
        vitima_id: vitimaId.trim(),
        agressor_id: agressorId.trim(),
        tipos_restricao: restricoesSelecionadas,
        prazo_dias: Number(prazoDias),
        distancia_minima_metros: distanciaMinima ? Number(distanciaMinima) : undefined,
        condicoes_especificas: condicoesEspecificas.trim() || undefined,
      });
      avisar(`Medida protetiva ${nova.numero_referencia} concedida com sucesso!`, 'sucesso');
      setModalConcederAberto(false);
      setOcorrenciaId('');
      setVitimaId('');
      setAgressorId('');
      carregarMedidas();
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    }
  };

  const executarRenovacao = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!medidaAlvo) return;
    if (justificativaRenovacao.trim().length < 10) {
      avisar('A justificativa técnica de prorrogação deve conter no mínimo 10 caracteres.', 'erro');
      return;
    }
    try {
      const atualizada = await medidasService.renovar(medidaAlvo.id, {
        dias_adicionais: Number(diasAdicionais),
        justificativa: justificativaRenovacao.trim(),
      });
      avisar(`Medida ${atualizada.numero_referencia} renovada por mais ${diasAdicionais} dias!`, 'sucesso');
      setModalRenovarAberto(false);
      carregarMedidas();
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    }
  };

  const executarRevogacao = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!medidaAlvo) return;
    if (motivoRevogacao.trim().length < 10) {
      avisar('O motivo da revogação deve conter no mínimo 10 caracteres.', 'erro');
      return;
    }
    try {
      const atualizada = await medidasService.revogar(medidaAlvo.id, {
        motivo: motivoRevogacao.trim(),
      });
      avisar(`Medida ${atualizada.numero_referencia} revogada!`, 'sucesso');
      setModalRevogarAberto(false);
      carregarMedidas();
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    }
  };

  const badgeDiasRestantes = (dias: number, status: string) => {
    if (status === 'REVOGADA') {
      return <span style={{ padding: '0.2rem 0.5rem', borderRadius: '4px', background: 'var(--surface-sunken)', color: 'var(--text-muted)', fontSize: '0.8rem', fontWeight: 600 }}>Revogada</span>;
    }
    if (dias <= 0) {
      return <span style={{ padding: '0.2rem 0.5rem', borderRadius: '4px', background: '#fee2e2', color: '#b91c1c', fontSize: '0.8rem', fontWeight: 700 }}>Vencida ({dias} dias)</span>;
    }
    if (dias <= 15) {
      return <span style={{ padding: '0.2rem 0.5rem', borderRadius: '4px', background: '#ffedd5', color: '#c2410c', fontSize: '0.8rem', fontWeight: 700 }}>⚠️ {dias} dias restantes</span>;
    }
    return <span style={{ padding: '0.2rem 0.5rem', borderRadius: '4px', background: '#dcfce7', color: '#15803d', fontSize: '0.8rem', fontWeight: 600 }}>{dias} dias de vigência</span>;
  };

  return (
    <div className="medidas-page" style={{ padding: '1.5rem', maxWidth: '1400px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '1.75rem', fontWeight: 700 }}>Medidas Protetivas de Urgência</h1>
          <p style={{ margin: '0.25rem 0 0', color: 'var(--text-muted)' }}>
            Vigilância ativa, prazos cautelares e imposição legal de restrições de proximidade (RF09 / UC09).
          </p>
        </div>
        {tem('DELEGADO') && (
          <button
            className="btn btn-primary"
            onClick={() => setModalConcederAberto(true)}
            style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.6rem 1.2rem', fontWeight: 600 }}
          >
            <span>+</span> Conceder Medida Protetiva
          </button>
        )}
      </div>

      {/* Barra de Filtros */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.25rem', borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem' }}>
        {['TODOS', 'ATIVA', 'RENOVADA', 'REVOGADA'].map((st) => (
          <button
            key={st}
            onClick={() => setFiltroStatus(st)}
            style={{
              padding: '0.4rem 0.8rem',
              borderRadius: '6px',
              border: 'none',
              background: filtroStatus === st ? 'var(--primary, #0284c7)' : 'transparent',
              color: filtroStatus === st ? '#fff' : 'var(--text)',
              cursor: 'pointer',
              fontWeight: 500,
            }}
          >
            {st === 'TODOS' ? 'Todas' : st === 'ATIVA' ? 'Ativas' : st === 'RENOVADA' ? 'Renovadas' : 'Revogadas'}
          </button>
        ))}
        <span style={{ marginLeft: 'auto', alignSelf: 'center', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
          Total registrado: <strong>{total}</strong>
        </span>
      </div>

      {/* Cards de Medidas */}
      {carregando ? (
        <p style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>Carregando medidas protetivas...</p>
      ) : medidas.length === 0 ? (
        <p style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>Nenhuma medida protetiva encontrada.</p>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: '1.25rem' }}>
          {medidas.map((m) => (
            <div
              key={m.id}
              style={{
                background: 'var(--surface)',
                borderRadius: '8px',
                border: '1px solid var(--border)',
                padding: '1.25rem',
                display: 'flex',
                flexDirection: 'column',
                boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                <span style={{ fontWeight: 700, fontSize: '1.1rem', color: 'var(--primary)' }}>{m.numero_referencia}</span>
                {badgeDiasRestantes(m.dias_restantes, m.status)}
              </div>

              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
                <div>Ocorrência: <strong>{m.ocorrencia_id.substring(0, 8)}...</strong></div>
                <div>Início: <strong>{m.data_inicio}</strong> &bull; Vencimento: <strong>{m.data_vencimento}</strong></div>
                {m.distancia_minima_metros && (
                  <div>Distância Mínima: <strong style={{ color: '#b91c1c' }}>{m.distancia_minima_metros} metros</strong></div>
                )}
              </div>

              {/* Tags de Restrição */}
              <div style={{ marginBottom: '1rem', display: 'flex', flexWrap: 'wrap', gap: '0.35rem' }}>
                {m.tipos_restricao.map((t) => (
                  <span
                    key={t}
                    style={{
                      fontSize: '0.75rem',
                      padding: '0.15rem 0.45rem',
                      borderRadius: '4px',
                      background: 'var(--surface-sunken)',
                      border: '1px solid var(--border)',
                    }}
                  >
                    {t.replace(/_/g, ' ')}
                  </span>
                ))}
              </div>

              {m.condicoes_especificas && (
                <div style={{ fontSize: '0.8rem', background: 'var(--surface-sunken)', padding: '0.5rem', borderRadius: '4px', marginBottom: '1rem' }}>
                  <em>"{m.condicoes_especificas}"</em>
                </div>
              )}

              {/* Rodapé e Ações do Delegado */}
              <div style={{ marginTop: 'auto', borderTop: '1px solid var(--border)', paddingTop: '0.75rem', display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
                {tem('DELEGADO') && m.status !== 'REVOGADA' && (
                  <>
                    <button
                      className="btn btn-sm btn-outline"
                      onClick={() => {
                        setMedidaAlvo(m);
                        setDiasAdicionais(30);
                        setJustificativaRenovacao('');
                        setModalRenovarAberto(true);
                      }}
                    >
                      Prorrogar
                    </button>
                    <button
                      className="btn btn-sm btn-ghost"
                      style={{ color: '#dc2626' }}
                      onClick={() => {
                        setMedidaAlvo(m);
                        setMotivoRevogacao('');
                        setModalRevogarAberto(true);
                      }}
                    >
                      Revogar
                    </button>
                  </>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal Conceder */}
      {modalConcederAberto && (
        <div className="modal-backdrop" style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000 }}>
          <div style={{ background: 'var(--surface)', padding: '1.5rem', borderRadius: '8px', maxWidth: '600px', width: '90%', maxHeight: '90vh', overflowY: 'auto' }}>
            <h2 style={{ marginTop: 0 }}>Formalizar Medida Protetiva de Urgência</h2>
            <form onSubmit={executarConcessao}>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontWeight: 600, marginBottom: '0.25rem' }}>ID da Ocorrência Policial *</label>
                <input
                  type="text"
                  className="form-control"
                  value={ocorrenciaId}
                  onChange={(e) => setOcorrenciaId(e.target.value)}
                  placeholder="UUID da ocorrência (ex: 7fbd82b6-...)"
                  style={{ width: '100%', padding: '0.5rem' }}
                  required
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                <div>
                  <label style={{ display: 'block', fontWeight: 600, marginBottom: '0.25rem' }}>ID da Vítima *</label>
                  <input
                    type="text"
                    className="form-control"
                    value={vitimaId}
                    onChange={(e) => setVitimaId(e.target.value)}
                    placeholder="UUID da vítima"
                    style={{ width: '100%', padding: '0.5rem' }}
                    required
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontWeight: 600, marginBottom: '0.25rem' }}>ID do Agressor *</label>
                  <input
                    type="text"
                    className="form-control"
                    value={agressorId}
                    onChange={(e) => setAgressorId(e.target.value)}
                    placeholder="UUID do agressor"
                    style={{ width: '100%', padding: '0.5rem' }}
                    required
                  />
                </div>
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontWeight: 600, marginBottom: '0.25rem' }}>Restrições Legais Impostas *</label>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', background: 'var(--surface-sunken)', padding: '0.75rem', borderRadius: '4px' }}>
                  {TIPOS_RESTRICAO_OPCOES.map((opt) => (
                    <label key={opt.id} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem' }}>
                      <input
                        type="checkbox"
                        checked={restricoesSelecionadas.includes(opt.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setRestricoesSelecionadas([...restricoesSelecionadas, opt.id]);
                          } else {
                            setRestricoesSelecionadas(restricoesSelecionadas.filter((id) => id !== opt.id));
                          }
                        }}
                      />
                      <span>{opt.label}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                <div>
                  <label style={{ display: 'block', fontWeight: 600, marginBottom: '0.25rem' }}>Prazo Inicial (Dias) *</label>
                  <input
                    type="number"
                    min="1"
                    max="730"
                    value={prazoDias}
                    onChange={(e) => setPrazoDias(Number(e.target.value))}
                    style={{ width: '100%', padding: '0.5rem' }}
                    required
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontWeight: 600, marginBottom: '0.25rem' }}>Distância Mínima (Metros)</label>
                  <input
                    type="number"
                    min="10"
                    max="50000"
                    value={distanciaMinima}
                    onChange={(e) => setDistanciaMinima(Number(e.target.value))}
                    style={{ width: '100%', padding: '0.5rem' }}
                  />
                </div>
              </div>

              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', fontWeight: 600, marginBottom: '0.25rem' }}>Condições Específicas / Observações</label>
                <textarea
                  className="form-control"
                  rows={3}
                  value={condicoesEspecificas}
                  onChange={(e) => setCondicoesEspecificas(e.target.value)}
                  placeholder="Orientações de rondas preventivas na residência ou local de trabalho..."
                  style={{ width: '100%', padding: '0.5rem' }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
                <button type="button" className="btn btn-ghost" onClick={() => setModalConcederAberto(false)}>Cancelar</button>
                <button type="submit" className="btn btn-primary">Conceder Medida</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal Renovar */}
      {modalRenovarAberto && medidaAlvo && (
        <div className="modal-backdrop" style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000 }}>
          <div style={{ background: 'var(--surface)', padding: '1.5rem', borderRadius: '8px', maxWidth: '500px', width: '90%' }}>
            <h2 style={{ marginTop: 0 }}>Prorrogar Medida — {medidaAlvo.numero_referencia}</h2>
            <form onSubmit={executarRenovacao}>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontWeight: 600, marginBottom: '0.25rem' }}>Dias Adicionais de Vigência *</label>
                <input
                  type="number"
                  min="1"
                  max="365"
                  value={diasAdicionais}
                  onChange={(e) => setDiasAdicionais(Number(e.target.value))}
                  style={{ width: '100%', padding: '0.5rem' }}
                  required
                />
              </div>

              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', fontWeight: 600, marginBottom: '0.25rem' }}>Justificativa Técnica / Policial *</label>
                <textarea
                  className="form-control"
                  rows={4}
                  value={justificativaRenovacao}
                  onChange={(e) => setJustificativaRenovacao(e.target.value)}
                  placeholder="Fundamente a necessidade da extensão de prazo..."
                  style={{ width: '100%', padding: '0.5rem' }}
                  required
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
                <button type="button" className="btn btn-ghost" onClick={() => setModalRenovarAberto(false)}>Cancelar</button>
                <button type="submit" className="btn btn-primary">Prorrogar Vigência</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal Revogar */}
      {modalRevogarAberto && medidaAlvo && (
        <div className="modal-backdrop" style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000 }}>
          <div style={{ background: 'var(--surface)', padding: '1.5rem', borderRadius: '8px', maxWidth: '500px', width: '90%' }}>
            <h2 style={{ marginTop: 0, color: '#dc2626' }}>Revogar Medida — {medidaAlvo.numero_referencia}</h2>
            <form onSubmit={executarRevogacao}>
              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', fontWeight: 600, marginBottom: '0.25rem' }}>Motivo da Revogação *</label>
                <textarea
                  className="form-control"
                  rows={4}
                  value={motivoRevogacao}
                  onChange={(e) => setMotivoRevogacao(e.target.value)}
                  placeholder="Fundamentação da extinção da cautelar..."
                  style={{ width: '100%', padding: '0.5rem' }}
                  required
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
                <button type="button" className="btn btn-ghost" onClick={() => setModalRevogarAberto(false)}>Cancelar</button>
                <button type="submit" className="btn btn-primary" style={{ background: '#dc2626', borderColor: '#dc2626' }}>Revogar Medida</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
export default MedidasProtetivasPage;
