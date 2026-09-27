import React, { useCallback, useEffect, useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../hooks/useToast';
import { mensagemDeErro } from '../services/api';
import {
  inqueritosService,
  type Inquerito,
  type ConexaoSugerida,
} from '../services/inqueritosService';
import { ocorrenciasService } from '../services/ocorrenciasService';
import { type OcorrenciaResumo } from '../types/api';

export const InqueritosPage: React.FC = () => {
  const { tem } = useAuth();
  const { avisar } = useToast();

  const [inqueritos, setInqueritos] = useState<Inquerito[]>([]);
  const [total, setTotal] = useState(0);
  const [filtroStatus, setFiltroStatus] = useState<string>('TODOS');
  const [carregando, setCarregando] = useState(false);

  // Inquérito selecionado para ver detalhes
  const [selecionado, setSelecionado] = useState<Inquerito | null>(null);

  // Modais
  const [modalInstaurarAberto, setModalInstaurarAberto] = useState(false);
  const [modalConcluirAberto, setModalConcluirAberto] = useState(false);
  const [modalVincularAberto, setModalVincularAberto] = useState(false);

  // Formulários
  const [ementa, setEmenta] = useState('');
  const [relatorioFinal, setRelatorioFinal] = useState('');
  const [ocorrenciasValidadas, setOcorrenciasValidadas] = useState<OcorrenciaResumo[]>([]);
  const [ocorrenciasSelecionadasIds, setOcorrenciasSelecionadasIds] = useState<string[]>([]);

  // Motor de sugestão de conexões
  const [sugestoes, setSugestoes] = useState<ConexaoSugerida[]>([]);
  const [carregandoSugestoes, setCarregandoSugestoes] = useState(false);

  const carregarInqueritos = useCallback(async () => {
    setCarregando(true);
    try {
      const statusParam = filtroStatus === 'TODOS' ? undefined : [filtroStatus];
      const res = await inqueritosService.listar({ status: statusParam });
      setInqueritos(res.itens);
      setTotal(res.total);
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    } finally {
      setCarregando(false);
    }
  }, [filtroStatus, avisar]);

  useEffect(() => {
    carregarInqueritos();
  }, [carregarInqueritos]);

  const carregarValidadas = async () => {
    try {
      const res = await ocorrenciasService.listar(['VALIDADA'], 50);
      setOcorrenciasValidadas(res.itens);
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    }
  };

  const abrirModalInstaurar = () => {
    setEmenta('');
    setOcorrenciasSelecionadasIds([]);
    carregarValidadas();
    setModalInstaurarAberto(true);
  };

  const executarInstauracao = async (e: React.FormEvent) => {
    e.preventDefault();
    if (ementa.trim().length < 10) {
      avisar('A ementa deve conter no mínimo 10 caracteres.', 'erro');
      return;
    }
    try {
      const novo = await inqueritosService.instaurar({
        ementa: ementa.trim(),
        ocorrencias_iniciais_ids: ocorrenciasSelecionadasIds,
      });
      avisar(`Inquérito ${novo.numero} instaurado com sucesso!`, 'sucesso');
      setModalInstaurarAberto(false);
      carregarInqueritos();
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    }
  };

  const selecionarInquerito = async (inq: Inquerito) => {
    setSelecionado(inq);
    setSugestoes([]);
    // Se o inquérito tem ocorrências, busca sugestões da primeira
    if (inq.ocorrencias.length > 0) {
      carregarSugestoesConexao(inq.ocorrencias[0].id);
    }
  };

  const carregarSugestoesConexao = async (ocorrenciaId: string) => {
    setCarregandoSugestoes(true);
    try {
      const res = await inqueritosService.buscarConexoes(ocorrenciaId);
      setSugestoes(res);
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    } finally {
      setCarregandoSugestoes(false);
    }
  };

  const executarVinculacao = async (ocorrenciaId: string) => {
    if (!selecionado) return;
    try {
      const atualizado = await inqueritosService.vincularOcorrencias(selecionado.id, [ocorrenciaId]);
      setSelecionado(atualizado);
      avisar('Ocorrência vinculada com sucesso ao inquérito!', 'sucesso');
      carregarInqueritos();
      // Atualiza sugestões
      carregarSugestoesConexao(ocorrenciaId);
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    }
  };

  const executarConclusao = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selecionado) return;
    if (relatorioFinal.trim().length < 10) {
      avisar('O relatório final deve conter no mínimo 10 caracteres.', 'erro');
      return;
    }
    try {
      const atualizado = await inqueritosService.concluir(selecionado.id, relatorioFinal.trim());
      setSelecionado(atualizado);
      setModalConcluirAberto(false);
      avisar(`Inquérito ${atualizado.numero} concluído com sucesso!`, 'sucesso');
      carregarInqueritos();
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    }
  };

  const badgeStatus = (status: string) => {
    switch (status) {
      case 'EM_ANDAMENTO':
        return <span className="status-badge" style={{ backgroundColor: 'var(--primary-bg, #e0f2fe)', color: 'var(--primary, #0284c7)' }}>Em andamento</span>;
      case 'CONCLUIDO':
        return <span className="status-badge" style={{ backgroundColor: 'var(--success-bg, #dcfce7)', color: 'var(--success, #16a34a)' }}>Concluído</span>;
      case 'ARQUIVADO':
        return <span className="status-badge" style={{ backgroundColor: 'var(--surface-sunken, #f1f5f9)', color: 'var(--text-muted, #64748b)' }}>Arquivado</span>;
      default:
        return <span className="status-badge">{status}</span>;
    }
  };

  return (
    <div className="inqueritos-page" style={{ padding: '1.5rem', maxWidth: '1400px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '1.75rem', fontWeight: 700 }}>Inquéritos Policiais (IP)</h1>
          <p style={{ margin: '0.25rem 0 0', color: 'var(--text-muted)' }}>
            Gestão formal de procedimentos investigativos criminais e correlação de fatos (RF06 / UC06).
          </p>
        </div>
        {tem('DELEGADO') && (
          <button
            className="btn btn-primary"
            onClick={abrirModalInstaurar}
            style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.6rem 1.2rem', fontWeight: 600 }}
          >
            <span>+</span> Instaurar Inquérito
          </button>
        )}
      </div>

      {/* Filtros por status */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem', borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem' }}>
        {['TODOS', 'EM_ANDAMENTO', 'CONCLUIDO', 'ARQUIVADO'].map((st) => (
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
            {st === 'TODOS' ? 'Todos' : st === 'EM_ANDAMENTO' ? 'Em Andamento' : st === 'CONCLUIDO' ? 'Concluídos' : 'Arquivados'}
          </button>
        ))}
        <span style={{ marginLeft: 'auto', alignSelf: 'center', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
          Total: {total}
        </span>
      </div>

      {/* Grid Principal */}
      <div style={{ display: 'grid', gridTemplateColumns: selecionado ? '1fr 1fr' : '1fr', gap: '1.5rem' }}>
        {/* Lista de Inquéritos */}
        <div style={{ background: 'var(--surface)', borderRadius: '8px', border: '1px solid var(--border)', padding: '1rem' }}>
          {carregando ? (
            <p style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>Carregando inquéritos...</p>
          ) : inqueritos.length === 0 ? (
            <p style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>Nenhum inquérito encontrado.</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {inqueritos.map((inq) => (
                <div
                  key={inq.id}
                  onClick={() => selecionarInquerito(inq)}
                  style={{
                    padding: '1rem',
                    borderRadius: '6px',
                    border: selecionado?.id === inq.id ? '2px solid var(--primary)' : '1px solid var(--border)',
                    background: selecionado?.id === inq.id ? 'var(--surface-hover, #f8fafc)' : 'var(--surface)',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                    <span style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--primary)' }}>{inq.numero}</span>
                    {badgeStatus(inq.status)}
                  </div>
                  <p style={{ margin: '0 0 0.5rem', fontSize: '0.95rem', color: 'var(--text)' }}>
                    {inq.ementa.length > 120 ? `${inq.ementa.substring(0, 120)}...` : inq.ementa}
                  </p>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    <span>Abertura: {new Date(inq.data_abertura).toLocaleDateString()}</span>
                    <span>{inq.ocorrencias.length} ocorrência(s) vinculada(s)</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Detalhes do Inquérito Selecionado */}
        {selecionado && (
          <div style={{ background: 'var(--surface)', borderRadius: '8px', border: '1px solid var(--border)', padding: '1.25rem', position: 'sticky', top: '1rem', maxHeight: 'calc(100vh - 2rem)', overflowY: 'auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '1px solid var(--border)', paddingBottom: '0.75rem', marginBottom: '1rem' }}>
              <div>
                <h2 style={{ margin: 0, fontSize: '1.3rem', color: 'var(--primary)' }}>{selecionado.numero}</h2>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                  Instaurado em {new Date(selecionado.data_abertura).toLocaleString()}
                </span>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                {badgeStatus(selecionado.status)}
                <button
                  onClick={() => setSelecionado(null)}
                  style={{ border: 'none', background: 'transparent', cursor: 'pointer', fontSize: '1.2rem', color: 'var(--text-muted)' }}
                >
                  &times;
                </button>
              </div>
            </div>

            <div style={{ marginBottom: '1rem' }}>
              <h4 style={{ margin: '0 0 0.25rem', fontSize: '0.9rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Ementa do Fato</h4>
              <p style={{ margin: 0, fontSize: '0.95rem', lineHeight: 1.5, background: 'var(--surface-sunken)', padding: '0.75rem', borderRadius: '4px' }}>
                {selecionado.ementa}
              </p>
            </div>

            {selecionado.relatorio_final && (
              <div style={{ marginBottom: '1rem' }}>
                <h4 style={{ margin: '0 0 0.25rem', fontSize: '0.9rem', color: 'var(--success)', textTransform: 'uppercase' }}>Relatório Conclusivo</h4>
                <p style={{ margin: 0, fontSize: '0.95rem', lineHeight: 1.5, background: 'var(--success-bg, #dcfce7)', padding: '0.75rem', borderRadius: '4px', color: 'var(--text)' }}>
                  {selecionado.relatorio_final}
                </p>
              </div>
            )}

            {/* Ocorrências Vinculadas */}
            <div style={{ marginBottom: '1.25rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 600 }}>Ocorrências Vinculadas ({selecionado.ocorrencias.length})</h3>
                {selecionado.status === 'EM_ANDAMENTO' && tem('DELEGADO') && (
                  <button
                    className="btn btn-sm btn-outline"
                    onClick={() => {
                      carregarValidadas();
                      setModalVincularAberto(true);
                    }}
                    style={{ fontSize: '0.8rem', padding: '0.2rem 0.6rem' }}
                  >
                    + Vincular Ocorrência
                  </button>
                )}
              </div>

              {selecionado.ocorrencias.length === 0 ? (
                <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                  Nenhuma ocorrência vinculada até o momento.
                </p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {selecionado.ocorrencias.map((oc) => (
                    <div
                      key={oc.id}
                      style={{
                        padding: '0.6rem 0.75rem',
                        border: '1px solid var(--border)',
                        borderRadius: '4px',
                        background: 'var(--surface)',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                      }}
                    >
                      <div>
                        <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{oc.numero_protocolo}</span>
                        <span style={{ margin: '0 0.5rem', color: 'var(--text-muted)' }}>&bull;</span>
                        <span style={{ fontSize: '0.85rem' }}>{oc.natureza}</span>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                          {oc.localizacao} &bull; {new Date(oc.data_hora_fato).toLocaleString()}
                        </div>
                      </div>
                      <button
                        className="btn btn-sm btn-ghost"
                        onClick={() => carregarSugestoesConexao(oc.id)}
                        title="Buscar conexões criminais semelhantes"
                        style={{ fontSize: '0.75rem' }}
                      >
                        🔍 Conexões
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Painel do Motor de Conexões Inteligentes */}
            {selecionado.status === 'EM_ANDAMENTO' && (
              <div style={{ marginBottom: '1.25rem', border: '1px solid var(--primary)', borderRadius: '6px', padding: '0.75rem', background: 'var(--primary-bg, #f0f9ff)' }}>
                <h4 style={{ margin: '0 0 0.5rem', color: 'var(--primary)', fontSize: '0.95rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <span>⚡</span> Sugestões de Conexões Criminais (IA/Motor)
                </h4>
                {carregandoSugestoes ? (
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Analisando cruzamento de dados...</p>
                ) : sugestoes.length === 0 ? (
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Nenhuma conexão forte sugerida no momento.</p>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {sugestoes.map((sug) => (
                      <div
                        key={sug.ocorrencia_id}
                        style={{
                          background: 'var(--surface)',
                          padding: '0.6rem',
                          borderRadius: '4px',
                          border: '1px solid var(--border)',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                        }}
                      >
                        <div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <span style={{ fontWeight: 600, fontSize: '0.85rem' }}>{sug.numero_protocolo}</span>
                            <span
                              style={{
                                fontSize: '0.75rem',
                                padding: '0.1rem 0.4rem',
                                borderRadius: '10px',
                                background: sug.score_similaridade >= 100 ? '#fecaca' : '#fed7aa',
                                color: sug.score_similaridade >= 100 ? '#b91c1c' : '#c2410c',
                                fontWeight: 700,
                              }}
                            >
                              Score: {sug.score_similaridade}
                            </span>
                          </div>
                          <div style={{ fontSize: '0.8rem', color: 'var(--text)' }}>{sug.natureza}</div>
                          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                            Motivos: {sug.motivos.join('; ')}
                          </div>
                        </div>
                        {tem('DELEGADO') && (
                          <button
                            className="btn btn-sm btn-primary"
                            onClick={() => executarVinculacao(sug.ocorrencia_id)}
                            style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem' }}
                          >
                            + Vincular
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Ações de Conclusão */}
            {selecionado.status === 'EM_ANDAMENTO' && tem('DELEGADO') && (
              <div style={{ borderTop: '1px solid var(--border)', paddingTop: '1rem', display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
                <button
                  className="btn btn-success"
                  onClick={() => {
                    setRelatorioFinal('');
                    setModalConcluirAberto(true);
                  }}
                  style={{ fontWeight: 600, padding: '0.5rem 1rem' }}
                >
                  Concluir Inquérito com Relatório Final
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Modal de Instauração */}
      {modalInstaurarAberto && (
        <div className="modal-backdrop" style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000 }}>
          <div style={{ background: 'var(--surface)', padding: '1.5rem', borderRadius: '8px', maxWidth: '600px', width: '90%', maxHeight: '90vh', overflowY: 'auto' }}>
            <h2 style={{ marginTop: 0 }}>Instaurar Inquérito Policial</h2>
            <form onSubmit={executarInstauracao}>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontWeight: 600, marginBottom: '0.25rem' }}>Ementa do Inquérito *</label>
                <textarea
                  className="form-control"
                  rows={4}
                  value={ementa}
                  onChange={(e) => setEmenta(e.target.value)}
                  placeholder="Descreva de forma clara e circunstanciada os fatos a serem investigados..."
                  style={{ width: '100%', padding: '0.5rem' }}
                  required
                />
              </div>

              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', fontWeight: 600, marginBottom: '0.25rem' }}>Vincular Ocorrências Iniciais (Validadas)</label>
                {ocorrenciasValidadas.length === 0 ? (
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Nenhuma ocorrência validada disponível.</p>
                ) : (
                  <div style={{ maxHeight: '180px', overflowY: 'auto', border: '1px solid var(--border)', borderRadius: '4px', padding: '0.5rem' }}>
                    {ocorrenciasValidadas.map((oc) => (
                      <label key={oc.ocorrencia_id} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.25rem 0', fontSize: '0.85rem' }}>
                        <input
                          type="checkbox"
                          checked={ocorrenciasSelecionadasIds.includes(oc.ocorrencia_id)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setOcorrenciasSelecionadasIds([...ocorrenciasSelecionadasIds, oc.ocorrencia_id]);
                            } else {
                              setOcorrenciasSelecionadasIds(ocorrenciasSelecionadasIds.filter((id) => id !== oc.ocorrencia_id));
                            }
                          }}
                        />
                        <span><strong>{oc.numero_protocolo}</strong> — {oc.natureza} ({new Date(oc.data_hora_fato).toLocaleDateString()})</span>
                      </label>
                    ))}
                  </div>
                )}
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
                <button type="button" className="btn btn-ghost" onClick={() => setModalInstaurarAberto(false)}>Cancelar</button>
                <button type="submit" className="btn btn-primary">Instaurar</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal de Conclusão */}
      {modalConcluirAberto && (
        <div className="modal-backdrop" style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000 }}>
          <div style={{ background: 'var(--surface)', padding: '1.5rem', borderRadius: '8px', maxWidth: '600px', width: '90%' }}>
            <h2 style={{ marginTop: 0 }}>Concluir Inquérito {selecionado?.numero}</h2>
            <form onSubmit={executarConclusao}>
              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', fontWeight: 600, marginBottom: '0.25rem' }}>Relatório Final Conclusivo *</label>
                <textarea
                  className="form-control"
                  rows={6}
                  value={relatorioFinal}
                  onChange={(e) => setRelatorioFinal(e.target.value)}
                  placeholder="Relatório detalhado sobre autoria, materialidade e indiciamento dos envolvidos..."
                  style={{ width: '100%', padding: '0.5rem' }}
                  required
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
                <button type="button" className="btn btn-ghost" onClick={() => setModalConcluirAberto(false)}>Cancelar</button>
                <button type="submit" className="btn btn-success">Homologar Conclusão</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal Vincular Ocorrência Avulsa */}
      {modalVincularAberto && (
        <div className="modal-backdrop" style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000 }}>
          <div style={{ background: 'var(--surface)', padding: '1.5rem', borderRadius: '8px', maxWidth: '600px', width: '90%' }}>
            <h2 style={{ marginTop: 0 }}>Vincular Ocorrência ao Inquérito</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Selecione uma ocorrência validada para associar a esta investigação:</p>

            <div style={{ maxHeight: '250px', overflowY: 'auto', border: '1px solid var(--border)', borderRadius: '4px', padding: '0.5rem', marginBottom: '1.5rem' }}>
              {ocorrenciasValidadas.map((oc) => (
                <div
                  key={oc.ocorrencia_id}
                  style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.5rem 0', borderBottom: '1px solid var(--border)' }}
                >
                  <span style={{ fontSize: '0.9rem' }}>
                    <strong>{oc.numero_protocolo}</strong> — {oc.natureza}
                  </span>
                  <button
                    className="btn btn-sm btn-primary"
                    onClick={async () => {
                      await executarVinculacao(oc.ocorrencia_id);
                      setModalVincularAberto(false);
                    }}
                  >
                    Vincular
                  </button>
                </div>
              ))}
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button type="button" className="btn btn-ghost" onClick={() => setModalVincularAberto(false)}>Fechar</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
export default InqueritosPage;
