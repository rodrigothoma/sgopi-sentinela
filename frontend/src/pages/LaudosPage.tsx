import React, { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../hooks/useToast';
import { mensagemDeErro } from '../services/api';
import { laudosService, type Laudo } from '../services/laudosService';

const TIPOS_PERICIA = [
  'BALISTICA',
  'TOXICOLOGICA',
  'LOCAL_CRIME',
  'VEICULAR',
  'NECROPSIA',
  'DOCUMENTOSCOPIA',
  'INFORMATICA_FORENSE',
  'OUTRA',
];

export const LaudosPage: React.FC = () => {
  const { t } = useTranslation(['laudos', 'common']);
  const { tem } = useAuth();
  const { avisar } = useToast();

  const [laudos, setLaudos] = useState<Laudo[]>([]);
  const [total, setTotal] = useState(0);
  const [carregando, setCarregando] = useState(false);

  // Filtros
  const [filtroStatus, setFiltroStatus] = useState<string>('TODOS');
  const [filtroTipo, setFiltroTipo] = useState<string>('TODOS');

  // Modais
  const [modalSolicitarAberto, setModalSolicitarAberto] = useState(false);
  const [modalAnexarAberto, setModalAnexarAberto] = useState(false);
  const [laudoParaAnexar, setLaudoParaAnexar] = useState<Laudo | null>(null);

  // Form Solicitar
  const [tipoPericia, setTipoPericia] = useState('BALISTICA');
  const [descricaoSolicitacao, setDescricaoSolicitacao] = useState('');
  const [ocorrenciaId, setOcorrenciaId] = useState('');

  // Form Anexar
  const [conclusoesTecnicas, setConclusoesTecnicas] = useState('');
  const [arquivoPdf, setArquivoPdf] = useState<File | null>(null);
  const [enviando, setEnviando] = useState(false);

  const carregarLaudos = useCallback(async () => {
    setCarregando(true);
    try {
      const statusParam = filtroStatus === 'TODOS' ? undefined : [filtroStatus];
      const res = await laudosService.listar({ status: statusParam });
      let lista = res.itens;
      if (filtroTipo !== 'TODOS') {
        lista = lista.filter((l) => l.tipo_pericia === filtroTipo);
      }
      setLaudos(lista);
      setTotal(res.total);
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    } finally {
      setCarregando(false);
    }
  }, [filtroStatus, filtroTipo, avisar]);

  useEffect(() => {
    carregarLaudos();
  }, [carregarLaudos]);

  const executarSolicitacao = async (e: React.FormEvent) => {
    e.preventDefault();
    if (descricaoSolicitacao.trim().length < 10) {
      avisar(t('laudos:validacoes.quesitos_min'), 'erro');
      return;
    }
    if (!ocorrenciaId.trim()) {
      avisar(t('laudos:validacoes.ocorrencia_obrigatoria'), 'erro');
      return;
    }
    try {
      await laudosService.solicitar({
        tipo_pericia: tipoPericia,
        descricao_solicitacao: descricaoSolicitacao.trim(),
        ocorrencia_id: ocorrenciaId.trim(),
      });
      avisar(t('laudos:notificacoes.solicitado_sucesso'), 'sucesso');
      setModalSolicitarAberto(false);
      setDescricaoSolicitacao('');
      setOcorrenciaId('');
      carregarLaudos();
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    }
  };

  const abrirModalAnexar = (laudo: Laudo) => {
    setLaudoParaAnexar(laudo);
    setConclusoesTecnicas('');
    setArquivoPdf(null);
    setModalAnexarAberto(true);
  };

  const executarAnexacao = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!laudoParaAnexar || !arquivoPdf) {
      avisar(t('laudos:validacoes.pdf_obrigatorio'), 'erro');
      return;
    }
    if (conclusoesTecnicas.trim().length < 10) {
      avisar(t('laudos:validacoes.conclusoes_min'), 'erro');
      return;
    }
    setEnviando(true);
    try {
      await laudosService.anexar(laudoParaAnexar.id, conclusoesTecnicas.trim(), arquivoPdf);
      avisar(t('laudos:notificacoes.anexado_sucesso'), 'sucesso');
      setModalAnexarAberto(false);
      carregarLaudos();
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    } finally {
      setEnviando(false);
    }
  };

  const renderBadgeStatus = (st: string) => {
    const texto = t(`laudos:status.${st}`, { defaultValue: st });
    return <span className={`badge badge-${st}`}>{texto}</span>;
  };

  return (
    <div className="laudos-page" style={{ padding: '1.5rem', maxWidth: '1400px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '1.75rem', fontWeight: 700, color: 'var(--ink)' }}>{t('laudos:titulo')}</h1>
          <p style={{ margin: '0.25rem 0 0', color: 'var(--muted)' }}>
            {t('laudos:subtitulo')}
          </p>
        </div>
        {tem('DELEGADO', 'PERITO') && (
          <button
            className="btn btn-primary"
            onClick={() => setModalSolicitarAberto(true)}
            style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.6rem 1.2rem', fontWeight: 600 }}
          >
            <span>+</span> {t('laudos:btn_solicitar')}
          </button>
        )}
      </div>

      {/* Filtros */}
      <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', marginBottom: '1.25rem', background: 'var(--card)', padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid var(--line)', flexWrap: 'wrap' }}>
        <div>
          <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--muted)', display: 'block', marginBottom: '0.2rem' }}>
            {t('laudos:filtros.status_label')}
          </label>
          <select
            value={filtroStatus}
            onChange={(e) => setFiltroStatus(e.target.value)}
            style={{ padding: '0.4rem 0.6rem', borderRadius: '6px', border: '1px solid var(--line)', background: 'var(--bg)', color: 'var(--ink)' }}
          >
            <option value="TODOS">{t('laudos:filtros.todos_status')}</option>
            <option value="SOLICITADO">{t('laudos:status.SOLICITADO')}</option>
            <option value="EM_ANALISE">{t('laudos:status.EM_ANALISE')}</option>
            <option value="CONCLUIDO">{t('laudos:status.CONCLUIDO')}</option>
          </select>
        </div>

        <div>
          <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--muted)', display: 'block', marginBottom: '0.2rem' }}>
            {t('laudos:filtros.especialidade_label')}
          </label>
          <select
            value={filtroTipo}
            onChange={(e) => setFiltroTipo(e.target.value)}
            style={{ padding: '0.4rem 0.6rem', borderRadius: '6px', border: '1px solid var(--line)', background: 'var(--bg)', color: 'var(--ink)' }}
          >
            <option value="TODOS">{t('laudos:filtros.todas_especialidades')}</option>
            {TIPOS_PERICIA.map((tp) => (
              <option key={tp} value={tp}>{t(`laudos:tipos.${tp}`, { defaultValue: tp.replace('_', ' ') })}</option>
            ))}
          </select>
        </div>

        <div style={{ marginLeft: 'auto', fontSize: '0.9rem', color: 'var(--muted)' }}>
          {t('laudos:total_registrado')}: <strong style={{ color: 'var(--ink)' }}>{total}</strong>
        </div>
      </div>

      {/* Lista de Laudos */}
      <div style={{ background: 'var(--card)', borderRadius: '8px', border: '1px solid var(--line)', overflow: 'hidden' }}>
        {carregando ? (
          <p style={{ textAlign: 'center', padding: '3rem', color: 'var(--muted)' }}>{t('laudos:carregando')}</p>
        ) : laudos.length === 0 ? (
          <p style={{ textAlign: 'center', padding: '3rem', color: 'var(--muted)' }}>{t('laudos:nenhum_encontrado')}</p>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
              <thead>
                <tr style={{ background: 'var(--card-hover)', borderBottom: '1px solid var(--line)' }}>
                  <th style={{ padding: '0.75rem 1rem', color: 'var(--ink)' }}>{t('laudos:tabela.numero')}</th>
                  <th style={{ padding: '0.75rem 1rem', color: 'var(--ink)' }}>{t('laudos:tabela.tipo')}</th>
                  <th style={{ padding: '0.75rem 1rem', color: 'var(--ink)' }}>{t('laudos:detalhes.demanda_quesitos')}</th>
                  <th style={{ padding: '0.75rem 1rem', color: 'var(--ink)' }}>{t('laudos:tabela.solicitado_em')}</th>
                  <th style={{ padding: '0.75rem 1rem', color: 'var(--ink)' }}>{t('laudos:tabela.status')}</th>
                  <th style={{ padding: '0.75rem 1rem', color: 'var(--ink)' }}>{t('laudos:tabela.hash')}</th>
                  <th style={{ padding: '0.75rem 1rem', textAlign: 'right', color: 'var(--ink)' }}>{t('laudos:tabela.acoes')}</th>
                </tr>
              </thead>
              <tbody>
                {laudos.map((l) => (
                  <tr key={l.id} style={{ borderBottom: '1px solid var(--line)' }}>
                    <td style={{ padding: '0.75rem 1rem', fontWeight: 700, color: 'var(--primary)' }}>
                      {l.numero_referencia}
                    </td>
                    <td style={{ padding: '0.75rem 1rem', color: 'var(--ink)' }}>
                      <span style={{ fontWeight: 600 }}>{t(`laudos:tipos.${l.tipo_pericia}`, { defaultValue: l.tipo_pericia.replace('_', ' ') })}</span>
                    </td>
                    <td style={{ padding: '0.75rem 1rem', maxWidth: '300px', color: 'var(--ink)' }}>
                      <div style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }} title={l.descricao_solicitacao}>
                        {l.descricao_solicitacao}
                      </div>
                    </td>
                    <td style={{ padding: '0.75rem 1rem', color: 'var(--muted)' }}>
                      {new Date(l.solicitado_em).toLocaleDateString()}
                    </td>
                    <td style={{ padding: '0.75rem 1rem' }}>
                      {renderBadgeStatus(l.status)}
                    </td>
                    <td style={{ padding: '0.75rem 1rem' }}>
                      {l.hash_sha256 ? (
                        <span
                          title={l.hash_sha256}
                          style={{
                            fontSize: '0.75rem',
                            fontFamily: 'monospace',
                            background: 'var(--card-hover)',
                            border: '1px solid var(--line)',
                            padding: '0.2rem 0.4rem',
                            borderRadius: '4px',
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '0.25rem',
                            color: 'var(--ink)',
                          }}
                        >
                          <span style={{ color: 'var(--ok)' }}>✔</span> {l.hash_sha256.substring(0, 12)}...
                        </span>
                      ) : (
                        <span style={{ color: 'var(--muted)', fontSize: '0.8rem' }}>{t('laudos:pendente_anexacao')}</span>
                      )}
                    </td>
                    <td style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>
                      {l.status === 'CONCLUIDO' ? (
                        <a
                          href={laudosService.downloadUrl(l.id)}
                          target="_blank"
                          rel="noreferrer"
                          className="btn btn-sm btn-outline"
                          style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}
                        >
                          <span>⬇</span> {t('laudos:acoes.download')}
                        </a>
                      ) : tem('PERITO', 'DELEGADO') ? (
                        <button
                          className="btn btn-sm btn-primary"
                          onClick={() => abrirModalAnexar(l)}
                        >
                          {t('laudos:acoes.anexar')}
                        </button>
                      ) : null}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal Requisitar Perícia */}
      {modalSolicitarAberto && (
        <div className="modal-backdrop" style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1200 }}>
          <div style={{ background: 'var(--card)', color: 'var(--ink)', padding: '1.5rem', borderRadius: '12px', border: '1px solid var(--line)', maxWidth: '600px', width: '90%', boxShadow: 'var(--shadow-pop)' }}>
            <h2 style={{ marginTop: 0, color: 'var(--ink)' }}>{t('laudos:modal_solicitar.titulo')}</h2>
            <p style={{ color: 'var(--muted)', fontSize: '0.9rem', marginTop: '-0.5rem', marginBottom: '1rem' }}>
              {t('laudos:modal_solicitar.subtitulo')}
            </p>
            <form onSubmit={executarSolicitacao}>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontWeight: 600, marginBottom: '0.25rem', color: 'var(--ink)' }}>
                  {t('laudos:modal_solicitar.campo_tipo')}
                </label>
                <select
                  value={tipoPericia}
                  onChange={(e) => setTipoPericia(e.target.value)}
                  style={{ width: '100%', padding: '0.6rem', borderRadius: '6px', border: '1px solid var(--line)', background: 'var(--bg)', color: 'var(--ink)' }}
                >
                  {TIPOS_PERICIA.map((tp) => (
                    <option key={tp} value={tp}>{t(`laudos:tipos.${tp}`, { defaultValue: tp.replace('_', ' ') })}</option>
                  ))}
                </select>
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontWeight: 600, marginBottom: '0.25rem', color: 'var(--ink)' }}>
                  {t('laudos:modal_solicitar.campo_ocorrencia')}
                </label>
                <input
                  type="text"
                  className="form-control"
                  value={ocorrenciaId}
                  onChange={(e) => setOcorrenciaId(e.target.value)}
                  placeholder={t('laudos:modal_solicitar.placeholder_ocorrencia')}
                  style={{ width: '100%', padding: '0.6rem', background: 'var(--bg)', color: 'var(--ink)', border: '1px solid var(--line)', borderRadius: '6px' }}
                  required
                />
              </div>

              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', fontWeight: 600, marginBottom: '0.25rem', color: 'var(--ink)' }}>
                  {t('laudos:modal_solicitar.campo_demanda')}
                </label>
                <textarea
                  className="form-control"
                  rows={4}
                  value={descricaoSolicitacao}
                  onChange={(e) => setDescricaoSolicitacao(e.target.value)}
                  placeholder={t('laudos:modal_solicitar.placeholder_demanda')}
                  style={{ width: '100%', padding: '0.6rem', background: 'var(--bg)', color: 'var(--ink)', border: '1px solid var(--line)', borderRadius: '6px' }}
                  required
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
                <button type="button" className="btn btn-ghost" onClick={() => setModalSolicitarAberto(false)}>{t('laudos:acoes.cancelar')}</button>
                <button type="submit" className="btn btn-primary">{t('laudos:modal_solicitar.btn_submit')}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal Anexar Laudo e Assinatura */}
      {modalAnexarAberto && laudoParaAnexar && (
        <div className="modal-backdrop" style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1200 }}>
          <div style={{ background: 'var(--card)', color: 'var(--ink)', padding: '1.5rem', borderRadius: '12px', border: '1px solid var(--line)', maxWidth: '600px', width: '90%', boxShadow: 'var(--shadow-pop)' }}>
            <h2 style={{ marginTop: 0, color: 'var(--ink)' }}>{t('laudos:modal_anexar.titulo')} — {laudoParaAnexar.numero_referencia}</h2>
            <p style={{ color: 'var(--muted)', fontSize: '0.9rem', marginTop: '-0.5rem', marginBottom: '1rem' }}>
              {t('laudos:modal_anexar.subtitulo')}
            </p>
            <form onSubmit={executarAnexacao}>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontWeight: 600, marginBottom: '0.25rem', color: 'var(--ink)' }}>
                  {t('laudos:modal_anexar.campo_arquivo')}
                </label>
                <input
                  type="file"
                  accept="application/pdf"
                  onChange={(e) => setArquivoPdf(e.target.files ? e.target.files[0] : null)}
                  style={{ width: '100%', padding: '0.5rem', background: 'var(--bg)', color: 'var(--ink)', border: '1px solid var(--line)', borderRadius: '6px' }}
                  required
                />
                <span style={{ fontSize: '0.8rem', color: 'var(--muted)', marginTop: '0.25rem', display: 'block' }}>
                  {t('laudos:modal_anexar.ajuda_arquivo')}
                </span>
              </div>

              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', fontWeight: 600, marginBottom: '0.25rem', color: 'var(--ink)' }}>
                  {t('laudos:modal_anexar.campo_conclusoes')}
                </label>
                <textarea
                  className="form-control"
                  rows={5}
                  value={conclusoesTecnicas}
                  onChange={(e) => setConclusoesTecnicas(e.target.value)}
                  placeholder={t('laudos:modal_anexar.placeholder_conclusoes')}
                  style={{ width: '100%', padding: '0.6rem', background: 'var(--bg)', color: 'var(--ink)', border: '1px solid var(--line)', borderRadius: '6px' }}
                  required
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
                <button type="button" className="btn btn-ghost" onClick={() => setModalAnexarAberto(false)} disabled={enviando}>{t('laudos:acoes.cancelar')}</button>
                <button type="submit" className="btn btn-primary" disabled={enviando}>
                  {enviando ? t('laudos:modal_anexar.submetendo') : t('laudos:modal_anexar.btn_submit')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default LaudosPage;
