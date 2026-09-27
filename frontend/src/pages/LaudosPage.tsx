import React, { useCallback, useEffect, useState } from 'react';
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
      avisar('A descrição dos quesitos deve conter no mínimo 10 caracteres.', 'erro');
      return;
    }
    if (!ocorrenciaId.trim()) {
      avisar('Informe o identificador da ocorrência de vínculo.', 'erro');
      return;
    }
    try {
      const novo = await laudosService.solicitar({
        tipo_pericia: tipoPericia,
        descricao_solicitacao: descricaoSolicitacao.trim(),
        ocorrencia_id: ocorrenciaId.trim(),
      });
      avisar(`Requisição de perícia ${novo.numero_referencia} emitida!`, 'sucesso');
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
      avisar('Selecione o arquivo PDF do laudo pericial.', 'erro');
      return;
    }
    if (conclusoesTecnicas.trim().length < 10) {
      avisar('As conclusões técnicas devem conter no mínimo 10 caracteres.', 'erro');
      return;
    }
    setEnviando(true);
    try {
      const concluido = await laudosService.anexar(laudoParaAnexar.id, conclusoesTecnicas.trim(), arquivoPdf);
      avisar(`Laudo ${concluido.numero_referencia} homologado e assinado com sucesso!`, 'sucesso');
      setModalAnexarAberto(false);
      carregarLaudos();
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    } finally {
      setEnviando(false);
    }
  };

  const badgeStatus = (st: string) => {
    switch (st) {
      case 'SOLICITADO':
        return <span className="status-badge" style={{ backgroundColor: '#fef3c7', color: '#b45309' }}>Solicitado</span>;
      case 'EM_ANALISE':
        return <span className="status-badge" style={{ backgroundColor: '#e0f2fe', color: '#0369a1' }}>Em Análise</span>;
      case 'CONCLUIDO':
        return <span className="status-badge" style={{ backgroundColor: '#dcfce7', color: '#15803d' }}>Concluído</span>;
      default:
        return <span className="status-badge">{st}</span>;
    }
  };

  return (
    <div className="laudos-page" style={{ padding: '1.5rem', maxWidth: '1400px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '1.75rem', fontWeight: 700 }}>Laudos Periciais — Polícia Científica</h1>
          <p style={{ margin: '0.25rem 0 0', color: 'var(--text-muted)' }}>
            Requisição de exames periciais, cadeia técnica de custódia e garantia de integridade SHA-256 (RF07 / UC07).
          </p>
        </div>
        {tem('DELEGADO', 'PERITO') && (
          <button
            className="btn btn-primary"
            onClick={() => setModalSolicitarAberto(true)}
            style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.6rem 1.2rem', fontWeight: 600 }}
          >
            <span>+</span> Requisitar Perícia
          </button>
        )}
      </div>

      {/* Filtros */}
      <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', marginBottom: '1.25rem', background: 'var(--surface)', padding: '0.75rem 1rem', borderRadius: '6px', border: '1px solid var(--border)' }}>
        <div>
          <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', display: 'block' }}>Status:</label>
          <select
            value={filtroStatus}
            onChange={(e) => setFiltroStatus(e.target.value)}
            style={{ padding: '0.35rem 0.6rem', borderRadius: '4px', border: '1px solid var(--border)', background: 'var(--surface)' }}
          >
            <option value="TODOS">Todos os Status</option>
            <option value="SOLICITADO">Solicitado</option>
            <option value="EM_ANALISE">Em Análise</option>
            <option value="CONCLUIDO">Concluído</option>
          </select>
        </div>

        <div>
          <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', display: 'block' }}>Especialidade Pericial:</label>
          <select
            value={filtroTipo}
            onChange={(e) => setFiltroTipo(e.target.value)}
            style={{ padding: '0.35rem 0.6rem', borderRadius: '4px', border: '1px solid var(--border)', background: 'var(--surface)' }}
          >
            <option value="TODOS">Todas as Especialidades</option>
            {TIPOS_PERICIA.map((tp) => (
              <option key={tp} value={tp}>{tp.replace('_', ' ')}</option>
            ))}
          </select>
        </div>

        <div style={{ marginLeft: 'auto', fontSize: '0.9rem', color: 'var(--text-muted)' }}>
          Total registrado: <strong>{total}</strong>
        </div>
      </div>

      {/* Lista de Laudos */}
      <div style={{ background: 'var(--surface)', borderRadius: '8px', border: '1px solid var(--border)', overflow: 'hidden' }}>
        {carregando ? (
          <p style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>Carregando laudos periciais...</p>
        ) : laudos.length === 0 ? (
          <p style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>Nenhum laudo pericial encontrado.</p>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
            <thead>
              <tr style={{ background: 'var(--surface-sunken)', borderBottom: '1px solid var(--border)' }}>
                <th style={{ padding: '0.75rem 1rem' }}>Número</th>
                <th style={{ padding: '0.75rem 1rem' }}>Especialidade</th>
                <th style={{ padding: '0.75rem 1rem' }}>Quesitos / Objeto</th>
                <th style={{ padding: '0.75rem 1rem' }}>Solicitado Em</th>
                <th style={{ padding: '0.75rem 1rem' }}>Status</th>
                <th style={{ padding: '0.75rem 1rem' }}>Integridade SHA-256</th>
                <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>Ações</th>
              </tr>
            </thead>
            <tbody>
              {laudos.map((l) => (
                <tr key={l.id} style={{ borderBottom: '1px solid var(--border)' }}>
                  <td style={{ padding: '0.75rem 1rem', fontWeight: 700, color: 'var(--primary)' }}>
                    {l.numero_referencia}
                  </td>
                  <td style={{ padding: '0.75rem 1rem' }}>
                    <span style={{ fontWeight: 600 }}>{l.tipo_pericia.replace('_', ' ')}</span>
                  </td>
                  <td style={{ padding: '0.75rem 1rem', maxWidth: '300px' }}>
                    <div style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }} title={l.descricao_solicitacao}>
                      {l.descricao_solicitacao}
                    </div>
                  </td>
                  <td style={{ padding: '0.75rem 1rem', color: 'var(--text-muted)' }}>
                    {new Date(l.solicitado_em).toLocaleDateString()}
                  </td>
                  <td style={{ padding: '0.75rem 1rem' }}>
                    {badgeStatus(l.status)}
                  </td>
                  <td style={{ padding: '0.75rem 1rem' }}>
                    {l.hash_sha256 ? (
                      <span
                        title={l.hash_sha256}
                        style={{
                          fontSize: '0.75rem',
                          fontFamily: 'monospace',
                          background: 'var(--surface-sunken)',
                          padding: '0.2rem 0.4rem',
                          borderRadius: '4px',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.25rem',
                        }}
                      >
                        <span style={{ color: 'var(--success)' }}>✔</span> {l.hash_sha256.substring(0, 12)}...
                      </span>
                    ) : (
                      <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>Pendente anexação</span>
                    )}
                  </td>
                  <td style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>
                    {l.status === 'CONCLUIDO' ? (
                      <a
                        href={laudosService.downloadUrl(l.id)}
                        target="_blank"
                        rel="noreferrer"
                        className="btn btn-sm btn-outline"
                        style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem', textDecoration: 'none' }}
                      >
                        <span>⬇</span> Ver Laudo PDF
                      </a>
                    ) : tem('PERITO', 'DELEGADO') ? (
                      <button
                        className="btn btn-sm btn-primary"
                        onClick={() => abrirModalAnexar(l)}
                      >
                        Anexar Conclusão
                      </button>
                    ) : null}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Modal Requisitar Perícia */}
      {modalSolicitarAberto && (
        <div className="modal-backdrop" style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000 }}>
          <div style={{ background: 'var(--surface)', padding: '1.5rem', borderRadius: '8px', maxWidth: '600px', width: '90%' }}>
            <h2 style={{ marginTop: 0 }}>Requisitar Perícia Técnica Oficial</h2>
            <form onSubmit={executarSolicitacao}>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontWeight: 600, marginBottom: '0.25rem' }}>Especialidade Pericial *</label>
                <select
                  value={tipoPericia}
                  onChange={(e) => setTipoPericia(e.target.value)}
                  style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--border)', background: 'var(--surface)' }}
                >
                  {TIPOS_PERICIA.map((tp) => (
                    <option key={tp} value={tp}>{tp.replace('_', ' ')}</option>
                  ))}
                </select>
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontWeight: 600, marginBottom: '0.25rem' }}>ID da Ocorrência Policial Vinculada *</label>
                <input
                  type="text"
                  className="form-control"
                  value={ocorrenciaId}
                  onChange={(e) => setOcorrenciaId(e.target.value)}
                  placeholder="UUID da ocorrência (ex: a5d9c5c4-...)"
                  style={{ width: '100%', padding: '0.5rem' }}
                  required
                />
              </div>

              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', fontWeight: 600, marginBottom: '0.25rem' }}>Descrição dos Quesitos e Fatos *</label>
                <textarea
                  className="form-control"
                  rows={4}
                  value={descricaoSolicitacao}
                  onChange={(e) => setDescricaoSolicitacao(e.target.value)}
                  placeholder="Detalhe o objeto a ser periciado e as perguntas técnicas da autoridade requisitante..."
                  style={{ width: '100%', padding: '0.5rem' }}
                  required
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
                <button type="button" className="btn btn-ghost" onClick={() => setModalSolicitarAberto(false)}>Cancelar</button>
                <button type="submit" className="btn btn-primary">Emitir Requisição</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal Anexar Laudo e Assinatura */}
      {modalAnexarAberto && laudoParaAnexar && (
        <div className="modal-backdrop" style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000 }}>
          <div style={{ background: 'var(--surface)', padding: '1.5rem', borderRadius: '8px', maxWidth: '600px', width: '90%' }}>
            <h2 style={{ marginTop: 0 }}>Anexar Laudo — {laudoParaAnexar.numero_referencia}</h2>
            <form onSubmit={executarAnexacao}>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontWeight: 600, marginBottom: '0.25rem' }}>Arquivo do Laudo Oficial (PDF) *</label>
                <input
                  type="file"
                  accept="application/pdf"
                  onChange={(e) => setArquivoPdf(e.target.files ? e.target.files[0] : null)}
                  style={{ width: '100%', padding: '0.5rem' }}
                  required
                />
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  O hash SHA-256 será calculado no momento do envio para garantir a cadeia de integridade imutável.
                </span>
              </div>

              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', fontWeight: 600, marginBottom: '0.25rem' }}>Conclusões Técnicas Periciais *</label>
                <textarea
                  className="form-control"
                  rows={5}
                  value={conclusoesTecnicas}
                  onChange={(e) => setConclusoesTecnicas(e.target.value)}
                  placeholder="Parecer final, constatações científicas e respostas aos quesitos formulados..."
                  style={{ width: '100%', padding: '0.5rem' }}
                  required
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
                <button type="button" className="btn btn-ghost" onClick={() => setModalAnexarAberto(false)} disabled={enviando}>Cancelar</button>
                <button type="submit" className="btn btn-success" disabled={enviando}>
                  {enviando ? 'Homologando e Calculando Hash...' : 'Homologar Laudo Técnico'}
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
