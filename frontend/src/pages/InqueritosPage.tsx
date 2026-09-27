import React, { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
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
  const { t } = useTranslation(['inqueritos', 'common']);
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
      avisar(t('inqueritos:validacoes.ementa_min'), 'erro');
      return;
    }
    try {
      await inqueritosService.instaurar({
        ementa: ementa.trim(),
        ocorrencias_iniciais_ids: ocorrenciasSelecionadasIds,
      });
      avisar(t('inqueritos:notificacoes.instaurado_sucesso'), 'sucesso');
      setModalInstaurarAberto(false);
      carregarInqueritos();
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
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

  const selecionarInquerito = async (inq: Inquerito) => {
    setSelecionado(inq);
    setSugestoes([]);
    // Se o inquérito tem ocorrências, busca sugestões da primeira
    if (inq.ocorrencias.length > 0) {
      carregarSugestoesConexao(inq.ocorrencias[0].id);
    }
  };

  const executarVinculacao = async (ocorrenciaId: string) => {
    if (!selecionado) return;
    try {
      const atualizado = await inqueritosService.vincularOcorrencias(selecionado.id, [ocorrenciaId]);
      setSelecionado(atualizado);
      avisar(t('inqueritos:notificacoes.vinculado_sucesso'), 'sucesso');
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
      avisar(t('inqueritos:validacoes.relatorio_min'), 'erro');
      return;
    }
    try {
      const atualizado = await inqueritosService.concluir(selecionado.id, relatorioFinal.trim());
      setSelecionado(atualizado);
      setModalConcluirAberto(false);
      avisar(t('inqueritos:notificacoes.concluido_sucesso'), 'sucesso');
      carregarInqueritos();
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    }
  };

  const renderBadgeStatus = (status: string) => {
    const texto = t(`inqueritos:status.${status}`, { defaultValue: status });
    return <span className={`badge badge-${status}`}>{texto}</span>;
  };

  return (
    <div className="inqueritos-page" style={{ padding: '1.5rem', maxWidth: '1400px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '1.75rem', fontWeight: 700, color: 'var(--ink)' }}>{t('inqueritos:titulo')}</h1>
          <p style={{ margin: '0.25rem 0 0', color: 'var(--muted)' }}>
            {t('inqueritos:subtitulo')}
          </p>
        </div>
        {tem('DELEGADO') && (
          <button
            className="btn btn-primary"
            onClick={abrirModalInstaurar}
            style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.6rem 1.2rem', fontWeight: 600 }}
          >
            <span>+</span> {t('inqueritos:btn_instaurar')}
          </button>
        )}
      </div>

      {/* Filtros por status */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem', borderBottom: '1px solid var(--line)', paddingBottom: '0.5rem', flexWrap: 'wrap' }}>
        {[
          { key: 'TODOS', label: t('inqueritos:filtros.todos') },
          { key: 'EM_ANDAMENTO', label: t('inqueritos:filtros.em_andamento') },
          { key: 'CONCLUIDO', label: t('inqueritos:filtros.concluidos') },
          { key: 'ARQUIVADO', label: t('inqueritos:filtros.arquivados') },
        ].map((item) => (
          <button
            key={item.key}
            onClick={() => setFiltroStatus(item.key)}
            style={{
              padding: '0.4rem 0.8rem',
              borderRadius: '6px',
              border: 'none',
              background: filtroStatus === item.key ? 'var(--primary)' : 'transparent',
              color: filtroStatus === item.key ? '#fff' : 'var(--ink)',
              cursor: 'pointer',
              fontWeight: 500,
              transition: 'background 0.15s ease',
            }}
          >
            {item.label}
          </button>
        ))}
        <span style={{ marginLeft: 'auto', alignSelf: 'center', color: 'var(--muted)', fontSize: '0.9rem' }}>
          {t('inqueritos:total')}: {total}
        </span>
      </div>

      {/* Grid Principal */}
      <div style={{ display: 'grid', gridTemplateColumns: selecionado ? '1fr 1fr' : '1fr', gap: '1.5rem' }}>
        {/* Lista de Inquéritos */}
        <div style={{ background: 'var(--card)', borderRadius: '8px', border: '1px solid var(--line)', padding: '1rem' }}>
          {carregando ? (
            <p style={{ textAlign: 'center', padding: '2rem', color: 'var(--muted)' }}>{t('inqueritos:carregando')}</p>
          ) : inqueritos.length === 0 ? (
            <p style={{ textAlign: 'center', padding: '2rem', color: 'var(--muted)' }}>{t('inqueritos:nenhum_encontrado')}</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {inqueritos.map((inq) => (
                <div
                  key={inq.id}
                  onClick={() => selecionarInquerito(inq)}
                  style={{
                    padding: '1rem',
                    borderRadius: '6px',
                    border: selecionado?.id === inq.id ? '2px solid var(--primary)' : '1px solid var(--line)',
                    background: selecionado?.id === inq.id ? 'var(--card-hover)' : 'var(--card)',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                    <span style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--primary)' }}>{inq.numero}</span>
                    {renderBadgeStatus(inq.status)}
                  </div>
                  <p style={{ margin: '0 0 0.5rem', fontSize: '0.95rem', color: 'var(--ink)' }}>
                    {inq.ementa.length > 120 ? `${inq.ementa.substring(0, 120)}...` : inq.ementa}
                  </p>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--muted)' }}>
                    <span>{t('inqueritos:tabela.data_abertura')}: {new Date(inq.data_abertura).toLocaleDateString()}</span>
                    <span>{inq.ocorrencias.length} {t('inqueritos:ocorrencias_vinculadas_qtd')}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Detalhes do Inquérito Selecionado */}
        {selecionado && (
          <div style={{ background: 'var(--card)', borderRadius: '8px', border: '1px solid var(--line)', padding: '1.25rem', position: 'sticky', top: '5rem', maxHeight: 'calc(100vh - 6rem)', overflowY: 'auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '1px solid var(--line)', paddingBottom: '0.75rem', marginBottom: '1rem' }}>
              <div>
                <h2 style={{ margin: 0, fontSize: '1.3rem', color: 'var(--primary)' }}>{selecionado.numero}</h2>
                <span style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>
                  {t('inqueritos:detalhes.data_abertura')}: {new Date(selecionado.data_abertura).toLocaleString()}
                </span>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                {renderBadgeStatus(selecionado.status)}
                <button
                  onClick={() => setSelecionado(null)}
                  style={{ border: 'none', background: 'transparent', cursor: 'pointer', fontSize: '1.2rem', color: 'var(--muted)' }}
                  aria-label={t('inqueritos:acoes.fechar')}
                >
                  &times;
                </button>
              </div>
            </div>

            <div style={{ marginBottom: '1rem' }}>
              <h4 style={{ margin: '0 0 0.25rem', fontSize: '0.9rem', color: 'var(--muted)', textTransform: 'uppercase' }}>
                {t('inqueritos:detalhes.descricao_linhas')}
              </h4>
              <p style={{ margin: 0, fontSize: '0.95rem', lineHeight: 1.5, background: 'var(--card-hover)', padding: '0.75rem', borderRadius: '4px', color: 'var(--ink)' }}>
                {selecionado.ementa}
              </p>
            </div>

            {selecionado.relatorio_final && (
              <div style={{ marginBottom: '1rem' }}>
                <h4 style={{ margin: '0 0 0.25rem', fontSize: '0.9rem', color: 'var(--ok)', textTransform: 'uppercase' }}>
                  {t('inqueritos:detalhes.relatorio_final')}
                </h4>
                <p style={{ margin: 0, fontSize: '0.95rem', lineHeight: 1.5, background: 'var(--card-hover)', borderLeft: '3px solid var(--ok)', padding: '0.75rem', borderRadius: '4px', color: 'var(--ink)' }}>
                  {selecionado.relatorio_final}
                </p>
              </div>
            )}

            {/* Ocorrências Vinculadas */}
            <div style={{ marginBottom: '1.25rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 600, color: 'var(--ink)' }}>
                  {t('inqueritos:detalhes.ocorrencias_vinculadas')} ({selecionado.ocorrencias.length})
                </h3>
                {selecionado.status === 'EM_ANDAMENTO' && tem('DELEGADO') && (
                  <button
                    className="btn btn-sm btn-outline"
                    onClick={() => {
                      carregarValidadas();
                      setModalVincularAberto(true);
                    }}
                    style={{ fontSize: '0.8rem', padding: '0.2rem 0.6rem' }}
                  >
                    + {t('inqueritos:acoes.vincular')}
                  </button>
                )}
              </div>

              {selecionado.ocorrencias.length === 0 ? (
                <p style={{ fontSize: '0.9rem', color: 'var(--muted)', fontStyle: 'italic' }}>
                  {t('inqueritos:nenhuma_ocorrencia')}
                </p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {selecionado.ocorrencias.map((oc) => (
                    <div
                      key={oc.id}
                      style={{
                        padding: '0.6rem 0.75rem',
                        border: '1px solid var(--line)',
                        borderRadius: '4px',
                        background: 'var(--card-hover)',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                      }}
                    >
                      <div>
                        <span style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--ink)' }}>{oc.numero_protocolo}</span>
                        <span style={{ margin: '0 0.5rem', color: 'var(--muted)' }}>&bull;</span>
                        <span style={{ fontSize: '0.85rem', color: 'var(--ink)' }}>{oc.natureza}</span>
                        <div style={{ fontSize: '0.75rem', color: 'var(--muted)', marginTop: '0.2rem' }}>
                          {oc.localizacao} &bull; {new Date(oc.data_hora_fato).toLocaleString()}
                        </div>
                      </div>
                      <button
                        className="btn btn-sm btn-ghost"
                        onClick={() => carregarSugestoesConexao(oc.id)}
                        title={t('inqueritos:acoes.buscar_conexoes')}
                        style={{ fontSize: '0.75rem' }}
                      >
                        🔍 {t('inqueritos:acoes.buscar_conexoes')}
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Painel do Motor de Conexões Inteligentes */}
            {selecionado.status === 'EM_ANDAMENTO' && (
              <div style={{ marginBottom: '1.25rem', border: '1px solid var(--primary-glow)', borderRadius: '6px', padding: '0.75rem', background: 'var(--card-hover)' }}>
                <h4 style={{ margin: '0 0 0.5rem', color: 'var(--primary)', fontSize: '0.95rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <span>⚡</span> {t('inqueritos:modal_conexoes.titulo')}
                </h4>
                {carregandoSugestoes ? (
                  <p style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>{t('inqueritos:modal_conexoes.subtitulo')}</p>
                ) : sugestoes.length === 0 ? (
                  <p style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>{t('inqueritos:modal_conexoes.nenhuma_sugestao')}</p>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {sugestoes.map((sug) => (
                      <div
                        key={sug.ocorrencia_id}
                        style={{
                          background: 'var(--card)',
                          padding: '0.6rem',
                          borderRadius: '4px',
                          border: '1px solid var(--line)',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                        }}
                      >
                        <div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <span style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--ink)' }}>{sug.numero_protocolo}</span>
                            <span
                              style={{
                                fontSize: '0.75rem',
                                padding: '0.1rem 0.4rem',
                                borderRadius: '10px',
                                background: sug.score_similaridade >= 100 ? 'rgba(239, 68, 68, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                                color: sug.score_similaridade >= 100 ? 'var(--danger)' : 'var(--warn)',
                                fontWeight: 700,
                              }}
                            >
                              {t('inqueritos:modal_conexoes.score')}: {sug.score_similaridade}
                            </span>
                          </div>
                          <div style={{ fontSize: '0.8rem', color: 'var(--ink)' }}>{sug.natureza}</div>
                          <div style={{ fontSize: '0.75rem', color: 'var(--muted)' }}>
                            {t('inqueritos:modal_conexoes.motivos')}: {sug.motivos.join('; ')}
                          </div>
                        </div>
                        {tem('DELEGADO') && (
                          <button
                            className="btn btn-sm btn-primary"
                            onClick={() => executarVinculacao(sug.ocorrencia_id)}
                            style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem' }}
                          >
                            + {t('inqueritos:acoes.vincular')}
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
              <div style={{ borderTop: '1px solid var(--line)', paddingTop: '1rem', display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
                <button
                  className="btn btn-primary"
                  onClick={() => {
                    setRelatorioFinal('');
                    setModalConcluirAberto(true);
                  }}
                  style={{ fontWeight: 600, padding: '0.5rem 1rem' }}
                >
                  {t('inqueritos:modal_concluir.btn_submit')}
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Modal de Instauração */}
      {modalInstaurarAberto && (
        <div className="modal-backdrop" style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1200 }}>
          <div style={{ background: 'var(--card)', color: 'var(--ink)', padding: '1.5rem', borderRadius: '12px', border: '1px solid var(--line)', maxWidth: '600px', width: '90%', maxHeight: '90vh', overflowY: 'auto', boxShadow: 'var(--shadow-pop)' }}>
            <h2 style={{ marginTop: 0, color: 'var(--ink)' }}>{t('inqueritos:modal_instaurar.titulo')}</h2>
            <form onSubmit={executarInstauracao}>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontWeight: 600, marginBottom: '0.25rem', color: 'var(--ink)' }}>
                  {t('inqueritos:modal_instaurar.campo_descricao')}
                </label>
                <textarea
                  className="form-control"
                  rows={4}
                  value={ementa}
                  onChange={(e) => setEmenta(e.target.value)}
                  placeholder={t('inqueritos:modal_instaurar.placeholder_descricao')}
                  style={{ width: '100%', padding: '0.6rem', background: 'var(--bg)', color: 'var(--ink)', border: '1px solid var(--line)', borderRadius: '6px' }}
                  required
                />
              </div>

              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', fontWeight: 600, marginBottom: '0.25rem', color: 'var(--ink)' }}>
                  {t('inqueritos:modal_vincular.titulo')}
                </label>
                {ocorrenciasValidadas.length === 0 ? (
                  <p style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>{t('inqueritos:modal_vincular.nenhuma_elegivel')}</p>
                ) : (
                  <div style={{ maxHeight: '180px', overflowY: 'auto', border: '1px solid var(--line)', borderRadius: '6px', padding: '0.5rem', background: 'var(--bg)' }}>
                    {ocorrenciasValidadas.map((oc) => (
                      <label key={oc.ocorrencia_id} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.35rem 0', fontSize: '0.85rem', color: 'var(--ink)', cursor: 'pointer' }}>
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
                <button type="button" className="btn btn-ghost" onClick={() => setModalInstaurarAberto(false)}>{t('inqueritos:acoes.cancelar')}</button>
                <button type="submit" className="btn btn-primary">{t('inqueritos:modal_instaurar.btn_submit')}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal de Conclusão */}
      {modalConcluirAberto && (
        <div className="modal-backdrop" style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1200 }}>
          <div style={{ background: 'var(--card)', color: 'var(--ink)', padding: '1.5rem', borderRadius: '12px', border: '1px solid var(--line)', maxWidth: '600px', width: '90%', boxShadow: 'var(--shadow-pop)' }}>
            <h2 style={{ marginTop: 0, color: 'var(--ink)' }}>{t('inqueritos:modal_concluir.titulo')} ({selecionado?.numero})</h2>
            <form onSubmit={executarConclusao}>
              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', fontWeight: 600, marginBottom: '0.25rem', color: 'var(--ink)' }}>
                  {t('inqueritos:modal_concluir.campo_relatorio')}
                </label>
                <textarea
                  className="form-control"
                  rows={6}
                  value={relatorioFinal}
                  onChange={(e) => setRelatorioFinal(e.target.value)}
                  placeholder={t('inqueritos:modal_concluir.placeholder_relatorio')}
                  style={{ width: '100%', padding: '0.6rem', background: 'var(--bg)', color: 'var(--ink)', border: '1px solid var(--line)', borderRadius: '6px' }}
                  required
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
                <button type="button" className="btn btn-ghost" onClick={() => setModalConcluirAberto(false)}>{t('inqueritos:acoes.cancelar')}</button>
                <button type="submit" className="btn btn-primary">{t('inqueritos:modal_concluir.btn_submit')}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal Vincular Ocorrência Avulsa */}
      {modalVincularAberto && (
        <div className="modal-backdrop" style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1200 }}>
          <div style={{ background: 'var(--card)', color: 'var(--ink)', padding: '1.5rem', borderRadius: '12px', border: '1px solid var(--line)', maxWidth: '600px', width: '90%', boxShadow: 'var(--shadow-pop)' }}>
            <h2 style={{ marginTop: 0, color: 'var(--ink)' }}>{t('inqueritos:modal_vincular.titulo')}</h2>
            <p style={{ color: 'var(--muted)', fontSize: '0.9rem' }}>{t('inqueritos:modal_vincular.subtitulo')}</p>

            <div style={{ maxHeight: '250px', overflowY: 'auto', border: '1px solid var(--line)', borderRadius: '6px', padding: '0.5rem', marginBottom: '1.5rem', background: 'var(--bg)' }}>
              {ocorrenciasValidadas.length === 0 ? (
                <p style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>{t('inqueritos:modal_vincular.nenhuma_elegivel')}</p>
              ) : (
                ocorrenciasValidadas.map((oc) => (
                  <div
                    key={oc.ocorrencia_id}
                    style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.5rem 0', borderBottom: '1px solid var(--line)' }}
                  >
                    <span style={{ fontSize: '0.9rem', color: 'var(--ink)' }}>
                      <strong>{oc.numero_protocolo}</strong> — {oc.natureza}
                    </span>
                    <button
                      className="btn btn-sm btn-primary"
                      onClick={async () => {
                        await executarVinculacao(oc.ocorrencia_id);
                        setModalVincularAberto(false);
                      }}
                    >
                      {t('inqueritos:acoes.vincular')}
                    </button>
                  </div>
                ))
              )}
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button type="button" className="btn btn-ghost" onClick={() => setModalVincularAberto(false)}>{t('inqueritos:acoes.fechar')}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default InqueritosPage;
