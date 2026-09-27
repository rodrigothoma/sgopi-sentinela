import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../hooks/useAuth';
import { useToast } from '../../hooks/useToast';
import { mensagemDeErro } from '../../services/api';
import { ocorrenciasService } from '../../services/ocorrenciasService';
import { laudosService } from '../../services/laudosService';
import { medidasService } from '../../services/medidasService';
import type { Evidencia, OcorrenciaDetalhe as Detalhe } from '../../types/api';
import { StatusBadge } from '../StatusBadge';
import { formatarNatureza } from '../../utils/formatarNatureza';
import { ApreensoesAba } from './ApreensoesAba';

const fmt = (iso: string) => new Date(iso).toLocaleString();

type EstadoVisual = 'CARREGANDO' | 'INTEGRA' | 'DIVERGENTE' | 'INDISPONIVEL' | 'ERRO';

const EvidenciaItem: React.FC<{ ocorrenciaId: string; evidencia: Evidencia }> = ({ ocorrenciaId, evidencia }) => {
  const { t } = useTranslation(['ocorrencias']);
  const [estado, setEstado] = useState<EstadoVisual>('CARREGANDO');
  const [erro, setErro] = useState<string | null>(null);
  const [baixando, setBaixando] = useState(false);

  useEffect(() => {
    let ativo = true;
    setEstado('CARREGANDO');
    setErro(null);
    ocorrenciasService.verificarIntegridade(ocorrenciaId, evidencia.id)
      .then((resultado) => { if (ativo) setEstado(resultado.estado); })
      .catch((falha) => {
        if (!ativo) return;
        const indisponivel = falha?.response?.status === 404;
        setEstado(indisponivel ? 'INDISPONIVEL' : 'ERRO');
        setErro(mensagemDeErro(falha, t('ocorrencias:evidencias.integridade_erro')));
      });
    return () => { ativo = false; };
  }, [ocorrenciaId, evidencia.id, t]);

  const baixar = async () => {
    setBaixando(true);
    setErro(null);
    try {
      await ocorrenciasService.baixarEvidencia(ocorrenciaId, evidencia);
    } catch (falha) {
      if (axios.isAxiosError(falha) && falha.response?.status === 409) setEstado('DIVERGENTE');
      if (axios.isAxiosError(falha) && falha.response?.status === 404) setEstado('INDISPONIVEL');
      setErro(mensagemDeErro(falha, t('ocorrencias:evidencias.download_erro')));
    } finally {
      setBaixando(false);
    }
  };

  const classe = estado === 'INTEGRA' ? 'ok' : estado === 'CARREGANDO' ? 'muted' : 'erro';
  return (
    <li className="evidencia-item">
      <div>
        <strong>{evidencia.nome_original}</strong> · {evidencia.formato.toUpperCase()} · {(evidencia.tamanho / 1024).toFixed(1)} KB · {fmt(evidencia.enviada_em)}
      </div>
      <div className="evidencia-hash"><strong>SHA-256:</strong> <code>{evidencia.hash_sha256}</code></div>
      <div className="evidencia-acoes">
        <span className={classe}>{t(`ocorrencias:evidencias.integridade_${estado.toLowerCase()}`)}</span>
        <button className="btn btn-sm" disabled={estado !== 'INTEGRA' || baixando} onClick={baixar}>
          {baixando ? t('ocorrencias:evidencias.baixando') : t('ocorrencias:evidencias.download')}
        </button>
      </div>
      {erro && <small className="erro">{erro}</small>}
    </li>
  );
};

type Aba = 'detalhe' | 'apreensoes';

interface Props {
  o: Detalhe;
  /** Chamado quando a aba de apreensões altera a ocorrência (novo item / custódia) para o pai recarregar o detalhe. */
  onAlterada?: () => void;
}

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

const TIPOS_RESTRICAO_OPCOES = [
  { id: 'AFASTAMENTO_DO_LAR', label: 'Afastamento do Lar / Domicílio' },
  { id: 'PROIBICAO_DE_CONTATO', label: 'Proibição de Contato por Qualquer Meio' },
  { id: 'LIMITE_DISTANCIA_METROS', label: 'Limite Mínimo de Distância (Metros)' },
  { id: 'SUSPENSAO_PORTE_ARMAS', label: 'Suspensão da Posse ou Porte de Armas' },
  { id: 'OUTRA', label: 'Outras Restrições Judiciais' },
];

export const OcorrenciaDetalheView: React.FC<Props> = ({ o, onAlterada }) => {
  const navigate = useNavigate();
  const { tem } = useAuth();
  const { avisar } = useToast();
  const { t } = useTranslation(['ocorrencias', 'common']);
  const [aba, setAba] = useState<Aba>('detalhe');
  const isOnline = o.envolvidos.some((e) => e.tipo === 'COMUNICANTE');

  // Modais de ações procedimentais
  const [modalLaudoAberto, setModalLaudoAberto] = useState(false);
  const [tipoPericia, setTipoPericia] = useState('LOCAL_CRIME');
  const [descricaoDemanda, setDescricaoDemanda] = useState('');
  const [enviandoLaudo, setEnviandoLaudo] = useState(false);

  const [modalMedidaAberta, setModalMedidaAberta] = useState(false);
  const [vitimaId, setVitimaId] = useState('');
  const [agressorId, setAgressorId] = useState('');
  const [prazoDias, setPrazoDias] = useState(90);
  const [restricoes, setRestricoes] = useState<string[]>(['AFASTAMENTO_DO_LAR', 'PROIBICAO_DE_CONTATO']);
  const [distanciaMetros, setDistanciaMetros] = useState<number>(500);
  const [observacoesMedida, setObservacoesMedida] = useState('');
  const [enviandoMedida, setEnviandoMedida] = useState(false);

  useEffect(() => {
    setAba('detalhe');
    const vitimas = o.envolvidos.filter((e) => e.tipo === 'VITIMA');
    const suspeitos = o.envolvidos.filter((e) => e.tipo === 'SUSPEITO');
    if (vitimas.length > 0) {
      setVitimaId(vitimas[0].id);
    } else if (o.envolvidos.length > 0) {
      setVitimaId(o.envolvidos[0].id);
    }
    if (suspeitos.length > 0) {
      setAgressorId(suspeitos[0].id);
    } else if (o.envolvidos.length > 1) {
      setAgressorId(o.envolvidos[1].id);
    }
  }, [o.ocorrencia_id, o.envolvidos]);

  const submeterLaudo = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!descricaoDemanda.trim()) {
      avisar('Informe a descrição da demanda pericial solicitada.', 'info');
      return;
    }
    setEnviandoLaudo(true);
    try {
      await laudosService.solicitar({
        ocorrencia_id: o.ocorrencia_id,
        tipo_pericia: tipoPericia,
        descricao_solicitacao: descricaoDemanda.trim(),
      });
      avisar('Requisição pericial protocolada com sucesso!', 'sucesso');
      setModalLaudoAberto(false);
      setDescricaoDemanda('');
      onAlterada?.();
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    } finally {
      setEnviandoLaudo(false);
    }
  };

  const alternarRestricao = (id: string) => {
    setRestricoes((atuais) =>
      atuais.includes(id) ? atuais.filter((r) => r !== id) : [...atuais, id],
    );
  };

  const submeterMedida = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!vitimaId || !agressorId) {
      avisar('Selecione a vítima e o agressor entre os envolvidos.', 'info');
      return;
    }
    if (vitimaId === agressorId) {
      avisar('A vítima e o agressor não podem ser a mesma pessoa.', 'erro');
      return;
    }
    if (restricoes.length === 0) {
      avisar('Selecione pelo menos um tipo de restrição cautelar.', 'info');
      return;
    }
    setEnviandoMedida(true);
    try {
      await medidasService.conceder({
        ocorrencia_id: o.ocorrencia_id,
        vitima_id: vitimaId,
        agressor_id: agressorId,
        tipos_restricao: restricoes,
        prazo_dias: prazoDias,
        distancia_minima_metros: restricoes.includes('LIMITE_DISTANCIA_METROS') ? distanciaMetros : undefined,
        condicoes_especificas: observacoesMedida.trim() || undefined,
      });
      avisar('Medida protetiva de urgência expedida com sucesso!', 'sucesso');
      setModalMedidaAberta(false);
      setObservacoesMedida('');
      onAlterada?.();
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    } finally {
      setEnviandoMedida(false);
    }
  };

  return (
    <div className="detalhe">
      <div className="detalhe-cabecalho">
        <h2>
          {o.numero_protocolo} <StatusBadge status={o.status} />
        </h2>
        <span className="muted">
          <span style={{ fontWeight: 600, color: isOnline ? 'var(--primary)' : 'inherit' }}>
            {isOnline ? t('ocorrencias:detalhe.canal_online') : t('ocorrencias:detalhe.canal_presencial')}
          </span>{' '}
          · {t('ocorrencias:detalhe.versao')} {o.versao} · {t('ocorrencias:detalhe.registrada_em')} {fmt(o.criada_em)}
        </span>
      </div>

      {/* Indicador de Vinculação com Inquérito Policial (RF06) */}
      {o.inquerito_id ? (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '12px 16px',
            margin: '12px 0 16px 0',
            borderRadius: 8,
            backgroundColor: 'rgba(99, 102, 241, 0.08)',
            border: '1px solid rgba(99, 102, 241, 0.3)',
          }}
        >
          <div>
            <span style={{ fontWeight: 600, color: 'var(--primary)', display: 'block' }}>
              📁 Vinculada ao Inquérito Policial
            </span>
            <small className="muted" style={{ fontFamily: 'monospace' }}>
              ID: {o.inquerito_id}
            </small>
          </div>
          <button
            type="button"
            className="btn btn-sm"
            onClick={() => navigate('/inqueritos')}
          >
            Abrir Inquéritos →
          </button>
        </div>
      ) : null}

      {/* Barra de Ações Rápidas do Delegado / Perito (RF06, RF07, RF09) */}
      <div
        style={{
          display: 'flex',
          gap: 8,
          flexWrap: 'wrap',
          alignItems: 'center',
          padding: '10px 14px',
          margin: '8px 0 16px 0',
          background: 'var(--surface-hover, rgba(255, 255, 255, 0.03))',
          borderRadius: 8,
          border: '1px solid var(--line, rgba(255, 255, 255, 0.08))',
        }}
      >
        <span style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--muted)', marginRight: 4 }}>
          Ações Procedimentais:
        </span>
        {tem('DELEGADO', 'PERITO') && (
          <button
            type="button"
            className="btn btn-sm"
            style={{ fontSize: '0.8rem', padding: '4px 10px' }}
            onClick={() => setModalLaudoAberto(true)}
          >
            🔬 Requisitar Laudo Pericial
          </button>
        )}
        {tem('DELEGADO') && (
          <button
            type="button"
            className="btn btn-sm"
            style={{ fontSize: '0.8rem', padding: '4px 10px' }}
            onClick={() => setModalMedidaAberta(true)}
          >
            🛡️ Conceder Medida Protetiva
          </button>
        )}
        {tem('DELEGADO') && !o.inquerito_id && (
          <button
            type="button"
            className="btn btn-sm"
            style={{ fontSize: '0.8rem', padding: '4px 10px' }}
            onClick={() => navigate('/inqueritos')}
          >
            📁 Vincular a Inquérito
          </button>
        )}
      </div>

      <div className="tabs detalhe-abas" role="tablist">
        <button role="tab" aria-selected={aba === 'detalhe'} className={`tab ${aba === 'detalhe' ? 'ativo' : ''}`} onClick={() => setAba('detalhe')}>
          {t('ocorrencias:detalhe.aba_detalhe')}
        </button>
        <button role="tab" aria-selected={aba === 'apreensoes'} className={`tab ${aba === 'apreensoes' ? 'ativo' : ''}`} onClick={() => setAba('apreensoes')} data-cy="tab-apreensoes">
          {t('ocorrencias:apreensoes.titulo')} ({o.itens_apreendidos.length})
        </button>
      </div>
      {aba === 'apreensoes' && <ApreensoesAba o={o} onAlterada={onAlterada} />}
      {aba === 'detalhe' && (<>
      <dl className="grid2">
        <dt>{t('ocorrencias:form.natureza_label')}</dt><dd>{formatarNatureza(o.natureza, t)}</dd>
        <dt>{t('ocorrencias:form.data_hora_fato_label')}</dt><dd>{fmt(o.data_hora_fato)}</dd>
        <dt>{t('ocorrencias:form.localizacao_label')}</dt><dd>{o.localizacao}</dd>
        <dt>{t('ocorrencias:form.coordenada_label')}</dt><dd>{o.latitude.toFixed(5)}, {o.longitude.toFixed(5)}</dd>
      </dl>
      <h4>{t('ocorrencias:form.descricao_label')}</h4>
      <p className="narrativa">{o.descricao}</p>
      {o.narrativa_integra !== null && (
        <p className={o.narrativa_integra ? 'ok' : 'erro'}>
          {o.narrativa_integra ? t('ocorrencias:detalhe.integra') : t('ocorrencias:detalhe.adulterada')} · SHA-256 {o.hash_narrativa?.slice(0, 12)}…
        </p>
      )}
      {o.justificativa_revisao && (
        <div className="callout">
          <strong>{t('ocorrencias:detalhe.justificativa')}:</strong> {o.justificativa_revisao}
        </div>
      )}
      {o.desfecho && (
        <div className="callout">
          <strong>{t('ocorrencias:detalhe.desfecho')}:</strong> {o.desfecho}
        </div>
      )}
      {o.motivo_arquivamento && (
        <div className="callout">
          <strong>{t('ocorrencias:detalhe.arquivada')}</strong> — {t('ocorrencias:detalhe.motivo')}: {o.motivo_arquivamento}
          {o.arquivada_por_id && <small className="muted"> · {t('ocorrencias:detalhe.por')} {o.arquivada_por_id.slice(0, 8)}</small>}
        </div>
      )}
      {o.motivo_exclusao && (
        <div className="alerta erro">
          <strong>{t('ocorrencias:detalhe.excluida')}</strong> — {t('ocorrencias:detalhe.motivo')}: {o.motivo_exclusao}
          {o.excluida_por_id && <small> · {t('ocorrencias:detalhe.por')} {o.excluida_por_id.slice(0, 8)}</small>}
        </div>
      )}
      <h4>{t('ocorrencias:form.envolvidos_label')}</h4>
      <ul className="lista">
        {o.envolvidos.map((e) => (
          <li key={e.id}>
            <strong>{e.nome}</strong> · {t(`ocorrencias:envolvido.${e.tipo}`, e.tipo)}
            {e.documento ? ` · ${e.documento}` : ''}
            {e.email ? ` · ${e.email}` : ''}
            {e.telefone ? ` · ${e.telefone}` : ''}
          </li>
        ))}
      </ul>
      {o.tipificacoes.length > 0 && (
        <>
          <h4>{t('ocorrencias:form.tipificacoes_label')}</h4>
          <ul className="lista">
            {o.tipificacoes.map((tp, i) => (
              <li key={i}><strong>{tp.artigo}</strong> — {tp.descricao}</li>
            ))}
          </ul>
        </>
      )}
      {o.evidencias.length > 0 && (
        <>
          <h4>{t('ocorrencias:evidencias.titulo')}</h4>
          <ul className="lista">
            {o.evidencias.map((e) => (
              <EvidenciaItem key={e.id} ocorrenciaId={o.ocorrencia_id} evidencia={e} />
            ))}
          </ul>
        </>
      )}
      <h4>{t('ocorrencias:detalhe.historico')}</h4>
      <ol className="historico">
        {o.historico_status.map((h, i) => (
          <li key={i}>
            <span className="muted">{fmt(h.em)}</span> {h.de ? <><StatusBadge status={h.de} /> → </> : null}
            <StatusBadge status={h.para} />
            {h.justificativa && <em> — {h.justificativa}</em>}
          </li>
        ))}
      </ol>
      </>)}

      {/* Modal Requisitar Laudo Pericial */}
      {modalLaudoAberto && (
        <div
          role="dialog"
          aria-modal="true"
          onClick={() => setModalLaudoAberto(false)}
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.65)',
            backdropFilter: 'blur(4px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 3000,
            padding: 16,
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              background: 'var(--card)',
              borderRadius: 16,
              border: '1px solid var(--line)',
              boxShadow: 'var(--shadow-pop)',
              width: '100%',
              maxWidth: 580,
              maxHeight: '90vh',
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden',
            }}
          >
            <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--line)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ margin: 0, fontSize: '1.1rem' }}>🔬 Requisitar Laudo Pericial Técnico</h3>
              <button type="button" className="btn btn-ghost btn-sm" onClick={() => setModalLaudoAberto(false)}>✕</button>
            </div>
            <form onSubmit={submeterLaudo} style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: 16, overflowY: 'auto' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 6 }}>
                  Ocorrência Vinculada
                </label>
                <input
                  type="text"
                  readOnly
                  value={`${o.numero_protocolo} — ${o.natureza}`}
                  style={{ width: '100%', padding: '8px 12px', borderRadius: 8, background: 'var(--bg)', border: '1px solid var(--line)', opacity: 0.8 }}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 6 }}>
                  Especialidade / Tipo de Perícia *
                </label>
                <select
                  value={tipoPericia}
                  onChange={(e) => setTipoPericia(e.target.value)}
                  style={{ width: '100%', padding: '8px 12px', borderRadius: 8, background: 'var(--card)', border: '1px solid var(--line)' }}
                >
                  {TIPOS_PERICIA.map((tp) => (
                    <option key={tp} value={tp}>{tp.replace(/_/g, ' ')}</option>
                  ))}
                </select>
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 6 }}>
                  Quesitos e Demanda Pericial Solicitada *
                </label>
                <textarea
                  rows={4}
                  value={descricaoDemanda}
                  onChange={(e) => setDescricaoDemanda(e.target.value)}
                  placeholder="Descreva detalhadamente o exame requerido pelo perito criminal ou autoridade..."
                  required
                  style={{ width: '100%', padding: '8px 12px', borderRadius: 8, background: 'var(--card)', border: '1px solid var(--line)' }}
                />
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 8 }}>
                <button type="button" className="btn btn-ghost" onClick={() => setModalLaudoAberto(false)} disabled={enviandoLaudo}>
                  Cancelar
                </button>
                <button type="submit" className="btn btn-primary" disabled={enviandoLaudo}>
                  {enviandoLaudo ? 'Protocolando...' : 'Requisitar Laudo'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal Conceder Medida Protetiva */}
      {modalMedidaAberta && (
        <div
          role="dialog"
          aria-modal="true"
          onClick={() => setModalMedidaAberta(false)}
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.65)',
            backdropFilter: 'blur(4px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 3000,
            padding: 16,
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              background: 'var(--card)',
              borderRadius: 16,
              border: '1px solid var(--line)',
              boxShadow: 'var(--shadow-pop)',
              width: '100%',
              maxWidth: 640,
              maxHeight: '90vh',
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden',
            }}
          >
            <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--line)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ margin: 0, fontSize: '1.1rem' }}>🛡️ Conceder Medida Protetiva de Urgência</h3>
              <button type="button" className="btn btn-ghost btn-sm" onClick={() => setModalMedidaAberta(false)}>✕</button>
            </div>
            <form onSubmit={submeterMedida} style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: 16, overflowY: 'auto' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 6 }}>
                    Vítima (Pessoa Protegida) *
                  </label>
                  <select
                    required
                    value={vitimaId}
                    onChange={(e) => setVitimaId(e.target.value)}
                    style={{ width: '100%', padding: '8px 12px', borderRadius: 8, background: 'var(--card)', border: '1px solid var(--line)' }}
                  >
                    <option value="">Selecione a vítima...</option>
                    {o.envolvidos.map((e) => (
                      <option key={e.id} value={e.id}>
                        {e.nome} ({e.tipo})
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 6 }}>
                    Agressor / Notificado (Investigado) *
                  </label>
                  <select
                    required
                    value={agressorId}
                    onChange={(e) => setAgressorId(e.target.value)}
                    style={{ width: '100%', padding: '8px 12px', borderRadius: 8, background: 'var(--card)', border: '1px solid var(--line)' }}
                  >
                    <option value="">Selecione o agressor...</option>
                    {o.envolvidos.map((e) => (
                      <option key={e.id} value={e.id}>
                        {e.nome} ({e.tipo})
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 6 }}>
                  Prazo de Vigência Inicial (Dias) *
                </label>
                <input
                  type="number"
                  min={1}
                  max={365}
                  value={prazoDias}
                  onChange={(e) => setPrazoDias(Number(e.target.value))}
                  style={{ width: '100%', padding: '8px 12px', borderRadius: 8, background: 'var(--card)', border: '1px solid var(--line)' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 8 }}>
                  Restrições Cautelares Aplicadas *
                </label>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {TIPOS_RESTRICAO_OPCOES.map((opt) => (
                    <label key={opt.id} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.9rem', cursor: 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={restricoes.includes(opt.id)}
                        onChange={() => alternarRestricao(opt.id)}
                      />
                      <span>{opt.label}</span>
                    </label>
                  ))}
                </div>
              </div>

              {restricoes.includes('LIMITE_DISTANCIA_METROS') && (
                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 6 }}>
                    Distância Mínima Cautelar (Metros) *
                  </label>
                  <input
                    type="number"
                    min={10}
                    step={10}
                    value={distanciaMetros}
                    onChange={(e) => setDistanciaMetros(Number(e.target.value))}
                    style={{ width: '100%', padding: '8px 12px', borderRadius: 8, background: 'var(--card)', border: '1px solid var(--line)' }}
                  />
                </div>
              )}

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 6 }}>
                  Observações / Especificações Judiciais
                </label>
                <textarea
                  rows={3}
                  value={observacoesMedida}
                  onChange={(e) => setObservacoesMedida(e.target.value)}
                  placeholder="Detalhes ou encaminhamentos para a central de monitoramento..."
                  style={{ width: '100%', padding: '8px 12px', borderRadius: 8, background: 'var(--card)', border: '1px solid var(--line)' }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 8 }}>
                <button type="button" className="btn btn-ghost" onClick={() => setModalMedidaAberta(false)} disabled={enviandoMedida}>
                  Cancelar
                </button>
                <button type="submit" className="btn btn-primary" disabled={enviandoMedida}>
                  {enviandoMedida ? 'Expedindo...' : 'Conceder Medida'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
