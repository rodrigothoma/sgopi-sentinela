import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../hooks/useAuth';
import { useToast } from '../../hooks/useToast';
import { mensagemDeErro } from '../../services/api';
import { ocorrenciasService } from '../../services/ocorrenciasService';
import { laudosService } from '../../services/laudosService';
import { medidasService } from '../../services/medidasService';
import type { Evidencia, IntegridadeEvidencia, OcorrenciaDetalhe as Detalhe } from '../../types/api';
import { StatusBadge } from '../StatusBadge';
import { formatarNatureza } from '../../utils/formatarNatureza';
import { ApreensoesAba } from './ApreensoesAba';
import { SpringCheck } from '../common/SpringCheck';
import { GlideSelect, type GlideSelectOption } from '../common/GlideSelect';
import { ComprovanteOcorrencia } from './ComprovanteOcorrencia';
import { formatarChave } from '../../utils/autenticidade';
import { formatarDataHora } from '../../utils/datas';

const fmt = (iso: string) => formatarDataHora(iso);

/**
 * NAO_VERIFICADA é o estado inicial: conferir a integridade relê o arquivo inteiro e grava auditoria
 * (append-only), então só acontece quando o usuário pede ou no download — nunca ao abrir o detalhe (N4).
 */
type EstadoVisual = 'NAO_VERIFICADA' | 'CARREGANDO' | 'INTEGRA' | 'DIVERGENTE' | 'INDISPONIVEL' | 'ERRO';

const EvidenciaItem: React.FC<{ ocorrenciaId: string; evidencia: Evidencia }> = ({ ocorrenciaId, evidencia }) => {
  const { t } = useTranslation(['ocorrencias']);
  const { avisar } = useToast();
  const [estado, setEstado] = useState<EstadoVisual>('NAO_VERIFICADA');
  const [resultado, setResultado] = useState<IntegridadeEvidencia | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [baixando, setBaixando] = useState(false);

  const verificarIntegridade = useCallback(async () => {
    setEstado('CARREGANDO');
    setResultado(null);
    setErro(null);
    try {
      const resultado = await ocorrenciasService.verificarIntegridade(ocorrenciaId, evidencia.id);
      setEstado(resultado.estado === 'ARQUIVO_AUSENTE' ? 'INDISPONIVEL' : resultado.estado);
      setResultado(resultado);
    } catch (falha) {
      const indisponivel = axios.isAxiosError(falha) && falha.response?.status === 404;
      setEstado(indisponivel ? 'INDISPONIVEL' : 'ERRO');
      setErro(mensagemDeErro(falha, t('ocorrencias:evidencias.integridade_erro')));
    }
  }, [evidencia.id, ocorrenciaId, t]);

  const baixar = async () => {
    setBaixando(true);
    setErro(null);
    try {
      await ocorrenciasService.baixarEvidencia(ocorrenciaId, evidencia);
      avisar(t('ocorrencias:evidencias.download_integridade_confirmada'), 'sucesso');
    } catch (falha) {
      if (axios.isAxiosError(falha) && [404, 409].includes(falha.response?.status ?? 0)) {
        setResultado(null);
        setEstado(falha.response?.status === 409 ? 'DIVERGENTE' : 'INDISPONIVEL');
      }
      setErro(mensagemDeErro(falha, t('ocorrencias:evidencias.download_erro')));
    } finally {
      setBaixando(false);
    }
  };

  const classe = estado === 'INTEGRA' ? 'ok' : estado === 'CARREGANDO' || estado === 'NAO_VERIFICADA' ? 'muted' : 'erro';
  return (
    <li className="evidencia-item">
      <div className="evidencia-metadados">
        <strong>{evidencia.nome_original}</strong>
        <span>{evidencia.formato.toUpperCase()} · {(evidencia.tamanho / 1024).toFixed(1)} KB</span>
        <span>{fmt(evidencia.enviada_em)}</span>
      </div>
      <div className="evidencia-integridade">
        <div className="evidencia-hash">
          <strong>{t('ocorrencias:evidencias.hash_armazenado')}:</strong>
          <code>{resultado?.hash_armazenado ?? evidencia.hash_sha256}</code>
        </div>
        {resultado && (
          <>
            <div className="evidencia-hash">
              <strong>{t('ocorrencias:evidencias.hash_recalculado')}:</strong>
              <code>{resultado.hash_recalculado}</code>
            </div>
            <div className="evidencia-integridade-resumo">
              <span className={resultado.estado === 'INTEGRA' ? 'ok' : 'erro'}>
                {t(`ocorrencias:evidencias.hashes_${resultado.estado === 'INTEGRA' ? 'correspondem' : 'divergem'}`)}
              </span>
              <span><strong>{t('ocorrencias:evidencias.verificado_em')}:</strong> {fmt(resultado.verificado_em)}</span>
            </div>
          </>
        )}
        {estado === 'INDISPONIVEL' && (
          <div className="evidencia-hash">
            <strong>{t('ocorrencias:evidencias.hash_recalculado')}:</strong>
            <span>{t('ocorrencias:evidencias.hash_indisponivel')}</span>
          </div>
        )}
      </div>
      <div className="evidencia-acoes">
        <span className={`${classe} evidencia-estado`}>
          {t(`ocorrencias:evidencias.integridade_${estado.toLowerCase()}`)}
        </span>
        <button
          type="button"
          className="btn btn-sm btn-outline"
          disabled={estado === 'CARREGANDO' || baixando}
          onClick={() => void verificarIntegridade()}
        >
          {estado === 'CARREGANDO'
            ? t('ocorrencias:evidencias.verificando')
            : estado === 'NAO_VERIFICADA'
              ? t('ocorrencias:evidencias.verificar')
              : t('ocorrencias:evidencias.verificar_novamente')}
        </button>
        {/* O download confere o SHA-256 no servidor: não depende de verificação prévia */}
        <button
          className="btn btn-sm"
          disabled={estado === 'CARREGANDO' || estado === 'DIVERGENTE' || estado === 'INDISPONIVEL' || baixando}
          onClick={baixar}
        >
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
  const { t } = useTranslation(['ocorrencias', 'inqueritos', 'laudos', 'medidas', 'common']);
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
  const [comprovante, setComprovante] = useState(false);
  const despachoValidacao = o.historico_status.find((registro) => registro.para === 'VALIDADA')?.justificativa;

  const opcoesTipoPericia: GlideSelectOption[] = useMemo(
    () =>
      TIPOS_PERICIA.map((tp) => ({
        value: tp,
        label: t(`laudos:tipos.${tp}`, { defaultValue: tp.replace(/_/g, ' ') }),
      })),
    [t],
  );

  const opcoesVitima: GlideSelectOption[] = useMemo(
    () => [
      { value: '', label: t('medidas:modal_conceder.placeholder_vitima') },
      ...o.envolvidos.map((e) => ({
        value: e.id,
        label: `${e.nome} (${t(`ocorrencias:envolvido.${e.tipo}`)})`,
      })),
    ],
    [o.envolvidos, t],
  );

  const opcoesAgressor: GlideSelectOption[] = useMemo(
    () => [
      { value: '', label: t('medidas:modal_conceder.placeholder_agressor') },
      ...o.envolvidos.map((e) => ({
        value: e.id,
        label: `${e.nome} (${t(`ocorrencias:envolvido.${e.tipo}`)})`,
      })),
    ],
    [o.envolvidos, t],
  );

  // Aba e comprovante voltam ao padrão só ao trocar de ocorrência: recarregar o detalhe da mesma
  // (ex.: após registrar uma apreensão) gera um novo array de envolvidos e não pode tirar o usuário da aba.
  useEffect(() => {
    setAba('detalhe');
    setComprovante(false);
  }, [o.ocorrencia_id]);

  useEffect(() => {
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
      avisar(t('laudos:validacoes.quesitos_min'), 'info');
      return;
    }
    setEnviandoLaudo(true);
    try {
      await laudosService.solicitar({
        ocorrencia_id: o.ocorrencia_id,
        tipo_pericia: tipoPericia,
        descricao_solicitacao: descricaoDemanda.trim(),
      });
      avisar(t('laudos:notificacoes.solicitado_sucesso'), 'sucesso');
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
      avisar(t('medidas:validacoes.campos_obrigatorios'), 'info');
      return;
    }
    if (vitimaId === agressorId) {
      avisar(t('medidas:validacoes.vitima_igual_agressor'), 'erro');
      return;
    }
    if (restricoes.length === 0) {
      avisar(t('medidas:validacoes.restricao_min'), 'info');
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
      avisar(t('medidas:notificacoes.concedida_sucesso'), 'sucesso');
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
          {t('ocorrencias:acoes_procedimentais.titulo')}
        </span>
        {tem('DELEGADO', 'PERITO') && (
          <button
            type="button"
            className="btn btn-sm"
            style={{ fontSize: '0.8rem', padding: '4px 10px' }}
            onClick={() => setModalLaudoAberto(true)}
          >
            🔬 {t('ocorrencias:acoes_procedimentais.requisitar_laudo')}
          </button>
        )}
        {tem('DELEGADO') && (
          <button
            type="button"
            className="btn btn-sm"
            style={{ fontSize: '0.8rem', padding: '4px 10px' }}
            onClick={() => setModalMedidaAberta(true)}
          >
            🛡️ {t('ocorrencias:acoes_procedimentais.conceder_medida')}
          </button>
        )}
        {tem('DELEGADO') && !o.inquerito_id && (
          <button
            type="button"
            className="btn btn-sm"
            style={{ fontSize: '0.8rem', padding: '4px 10px' }}
            onClick={() => navigate('/inqueritos')}
          >
            📁 {t('ocorrencias:acoes_procedimentais.vincular_inquerito')}
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
      {o.chave_autenticidade && (
        <div className="callout comprovante-callout" data-cy="documento-emitido">
          <div>
            <strong>{t('ocorrencias:comprovante.chave')}:</strong> <code data-cy="chave-autenticidade">{formatarChave(o.chave_autenticidade)}</code>
            <br /><small className="muted">{t('ocorrencias:comprovante.dica')}</small>
          </div>
          <button className="btn btn-sm" onClick={() => setComprovante(true)} data-cy="emitir-comprovante">
            {t('ocorrencias:comprovante.emitir')}
          </button>
        </div>
      )}
      {comprovante && o.chave_autenticidade && (
        <ComprovanteOcorrencia o={o} chave={o.chave_autenticidade} onFechar={() => setComprovante(false)} />
      )}
      {despachoValidacao && (
        <div className="callout">
          <strong>{t('ocorrencias:detalhe.despacho')}:</strong> {despachoValidacao}
        </div>
      )}
      {o.justificativa_revisao && !despachoValidacao && (
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
            {h.justificativa && (
              <em> — {h.para === 'VALIDADA' ? `${t('ocorrencias:detalhe.despacho')}: ` : ''}{h.justificativa}</em>
            )}
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
              <h3 style={{ margin: 0, fontSize: '1.1rem' }}>🔬 {t('laudos:modal_solicitar.titulo')}</h3>
              <button type="button" className="btn btn-ghost btn-sm" onClick={() => setModalLaudoAberto(false)}>✕</button>
            </div>
            <form onSubmit={submeterLaudo} style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: 16, overflowY: 'auto' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 6 }}>
                  {t('laudos:modal_solicitar.campo_ocorrencia')}
                </label>
                <input
                  type="text"
                  readOnly
                  value={`${o.numero_protocolo} — ${formatarNatureza(o.natureza, t)}`}
                  style={{ width: '100%', height: '42px', padding: '8px 12px', borderRadius: 8, background: 'var(--bg)', border: '1px solid var(--line)', opacity: 0.8 }}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 6 }}>
                  {t('laudos:modal_solicitar.campo_tipo')}
                </label>
                <GlideSelect
                  value={tipoPericia}
                  options={opcoesTipoPericia}
                  onChange={(val) => setTipoPericia(val)}
                  fullWidth
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 6 }}>
                  {t('laudos:modal_solicitar.campo_demanda')}
                </label>
                <textarea
                  rows={4}
                  value={descricaoDemanda}
                  onChange={(e) => setDescricaoDemanda(e.target.value)}
                  placeholder={t('laudos:modal_solicitar.placeholder_demanda')}
                  required
                  style={{ width: '100%', padding: '8px 12px', borderRadius: 8, background: 'var(--card)', border: '1px solid var(--line)' }}
                />
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 8 }}>
                <button type="button" className="btn btn-ghost" onClick={() => setModalLaudoAberto(false)} disabled={enviandoLaudo}>
                  {t('common:actions.cancel')}
                </button>
                <button type="submit" className="btn btn-primary" disabled={enviandoLaudo}>
                  {enviandoLaudo ? t('laudos:modal_solicitar.submetendo') : t('laudos:modal_solicitar.btn_submit')}
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
              <h3 style={{ margin: 0, fontSize: '1.1rem' }}>🛡️ {t('medidas:modal_conceder.titulo')}</h3>
              <button type="button" className="btn btn-ghost btn-sm" onClick={() => setModalMedidaAberta(false)}>✕</button>
            </div>
            <form onSubmit={submeterMedida} style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: 16, overflowY: 'auto' }}>
              {o.envolvidos.length < 2 && (
                <div className="alerta" role="status">
                  {t('medidas:modal_conceder.envolvidos_insuficientes', { quantidade: o.envolvidos.length })}
                </div>
              )}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 6 }}>
                    {t('medidas:modal_conceder.campo_vitima')}
                  </label>
                  <GlideSelect
                    value={vitimaId}
                    options={opcoesVitima}
                    onChange={(val) => setVitimaId(val)}
                    placeholder={t('medidas:modal_conceder.placeholder_vitima')}
                    fullWidth
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 6 }}>
                    {t('medidas:modal_conceder.campo_agressor')}
                  </label>
                  <GlideSelect
                    value={agressorId}
                    options={opcoesAgressor}
                    onChange={(val) => setAgressorId(val)}
                    placeholder={t('medidas:modal_conceder.placeholder_agressor')}
                    fullWidth
                  />
                </div>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 6 }}>
                  {t('medidas:modal_conceder.campo_prazo')}
                </label>
                <input
                  type="number"
                  min={1}
                  max={365}
                  value={prazoDias}
                  onChange={(e) => setPrazoDias(Number(e.target.value))}
                  style={{ width: '100%', height: '42px', padding: '8px 12px', borderRadius: 8, background: 'var(--card)', border: '1px solid var(--line)' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 8 }}>
                  {t('medidas:modal_conceder.campo_restricoes')}
                </label>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '8px' }}>
                  {TIPOS_RESTRICAO_OPCOES.map((opt) => {
                    const isChecked = restricoes.includes(opt.id);
                    return (
                      <div
                        key={opt.id}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          minHeight: '42px',
                          padding: '0 10px',
                          borderRadius: '6px',
                          background: isChecked ? 'var(--card-hover)' : 'transparent',
                          border: isChecked ? '1px solid var(--primary)' : '1px solid var(--line)',
                          transition: 'all 0.15s ease',
                          cursor: 'pointer',
                        }}
                        onClick={() => alternarRestricao(opt.id)}
                      >
                        <SpringCheck
                          checked={isChecked}
                          strike="none"
                          label={t(`medidas:restricoes.${opt.id}`, { defaultValue: opt.label })}
                          onChange={() => alternarRestricao(opt.id)}
                        />
                      </div>
                    );
                  })}
                </div>
              </div>

              {restricoes.includes('LIMITE_DISTANCIA_METROS') && (
                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 6 }}>
                    {t('medidas:modal_conceder.campo_distancia')}
                  </label>
                  <input
                    type="number"
                    min={10}
                    step={10}
                    value={distanciaMetros}
                    onChange={(e) => setDistanciaMetros(Number(e.target.value))}
                    style={{ width: '100%', height: '42px', padding: '8px 12px', borderRadius: 8, background: 'var(--card)', border: '1px solid var(--line)' }}
                  />
                </div>
              )}

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 6 }}>
                  {t('medidas:modal_conceder.campo_condicoes')}
                </label>
                <textarea
                  rows={3}
                  value={observacoesMedida}
                  onChange={(e) => setObservacoesMedida(e.target.value)}
                  placeholder={t('medidas:modal_conceder.placeholder_condicoes')}
                  style={{ width: '100%', padding: '8px 12px', borderRadius: 8, background: 'var(--card)', border: '1px solid var(--line)' }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 8 }}>
                <button type="button" className="btn btn-ghost" onClick={() => setModalMedidaAberta(false)} disabled={enviandoMedida}>
                  {t('common:actions.cancel')}
                </button>
                <button type="submit" className="btn btn-primary" disabled={enviandoMedida}>
                  {enviandoMedida ? t('medidas:modal_conceder.submetendo') : t('medidas:modal_conceder.btn_submit')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
