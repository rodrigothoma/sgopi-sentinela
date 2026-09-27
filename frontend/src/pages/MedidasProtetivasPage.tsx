import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../hooks/useToast';
import { mensagemDeErro } from '../services/api';
import { medidasService, type MedidaProtetiva } from '../services/medidasService';
import { ocorrenciasService } from '../services/ocorrenciasService';
import type { OcorrenciaResumo, EnvolvidoDetalhe } from '../types/api';
import { SpringCheck } from '../components/common/SpringCheck';
import { GlideSelect, type GlideSelectOption } from '../components/common/GlideSelect';

const TIPOS_RESTRICAO_CHAVES = [
  'AFASTAMENTO_DO_LAR',
  'PROIBICAO_DE_CONTATO',
  'LIMITE_DISTANCIA_METROS',
  'SUSPENSAO_PORTE_ARMAS',
  'OUTRA',
];

export const MedidasProtetivasPage: React.FC = () => {
  const { t } = useTranslation(['medidas', 'common']);
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

  // Seleção e Envolvidos da Ocorrência no Modal Conceder
  const [listaOcorrencias, setListaOcorrencias] = useState<OcorrenciaResumo[]>([]);
  const [modoManualOcorrencia, setModoManualOcorrencia] = useState(false);
  const [envolvidosOcorrencia, setEnvolvidosOcorrencia] = useState<EnvolvidoDetalhe[]>([]);
  const [carregandoEnvolvidos, setCarregandoEnvolvidos] = useState(false);
  const [modoManualVitima, setModoManualVitima] = useState(false);
  const [modoManualAgressor, setModoManualAgressor] = useState(false);

  // Form Renovar
  const [diasAdicionais, setDiasAdicionais] = useState<number>(30);
  const [justificativaRenovacao, setJustificativaRenovacao] = useState('');

  // Form Revogar
  const [motivoRevogacao, setMotivoRevogacao] = useState('');

  const opcoesStatusMedidas: GlideSelectOption[] = useMemo(
    () => [
      { value: 'TODOS', label: t('medidas:filtros.todas') },
      { value: 'ATIVA', label: t('medidas:filtros.ativas') },
      { value: 'RENOVADA', label: t('medidas:filtros.renovadas') },
      { value: 'REVOGADA', label: t('medidas:filtros.revogadas') },
    ],
    [t],
  );

  const opcoesOcorrenciasModal: GlideSelectOption[] = useMemo(() => {
    return listaOcorrencias.map((oc) => {
      const loc = oc.localizacao
        ? oc.localizacao.length > 25
          ? `${oc.localizacao.slice(0, 22)}...`
          : oc.localizacao
        : 'Sem local';
      const labelCompleto = `${oc.numero_protocolo} — ${oc.natureza} (${loc})`;
      const labelFormatado = labelCompleto.length > 55 ? `${labelCompleto.slice(0, 52)}...` : labelCompleto;
      return {
        value: oc.ocorrencia_id,
        label: labelFormatado,
      };
    });
  }, [listaOcorrencias]);

  const opcoesVitimasModal: GlideSelectOption[] = useMemo(() => {
    return envolvidosOcorrencia.map((env) => {
      const nomeCurto = env.nome.length > 20 ? `${env.nome.slice(0, 17)}...` : env.nome;
      const doc = env.documento ? ` · ${env.documento}` : '';
      const labelCompleto = `${nomeCurto} (${env.tipo}${doc})`;
      const labelFormatado = labelCompleto.length > 30 ? `${labelCompleto.slice(0, 27)}...` : labelCompleto;
      return {
        value: env.id,
        label: labelFormatado,
      };
    });
  }, [envolvidosOcorrencia]);

  const opcoesAgressoresModal: GlideSelectOption[] = useMemo(() => {
    return envolvidosOcorrencia.map((env) => {
      const nomeCurto = env.nome.length > 20 ? `${env.nome.slice(0, 17)}...` : env.nome;
      const doc = env.documento ? ` · ${env.documento}` : '';
      const labelCompleto = `${nomeCurto} (${env.tipo}${doc})`;
      const labelFormatado = labelCompleto.length > 30 ? `${labelCompleto.slice(0, 27)}...` : labelCompleto;
      return {
        value: env.id,
        label: labelFormatado,
      };
    });
  }, [envolvidosOcorrencia]);

  const abrirModalConceder = async () => {
    setOcorrenciaId('');
    setVitimaId('');
    setAgressorId('');
    setEnvolvidosOcorrencia([]);
    setModoManualOcorrencia(false);
    setModoManualVitima(false);
    setModoManualAgressor(false);
    setRestricoesSelecionadas(['AFASTAMENTO_DO_LAR', 'PROIBICAO_DE_CONTATO']);
    setPrazoDias(90);
    setDistanciaMinima(300);
    setCondicoesEspecificas('');
    setModalConcederAberto(true);
    try {
      const res = await ocorrenciasService.listar([], 100);
      setListaOcorrencias(res.itens);
    } catch {
      // Falha silenciosa
    }
  };

  const selecionarOuCarregarOcorrencia = async (id: string) => {
    setOcorrenciaId(id);
    if (!id || id.trim() === '') {
      setEnvolvidosOcorrencia([]);
      return;
    }
    setCarregandoEnvolvidos(true);
    try {
      const detalhe = await ocorrenciasService.buscarPorId(id.trim());
      const envs = detalhe.envolvidos || [];
      setEnvolvidosOcorrencia(envs);
      const primeiraVitima = envs.find((e) => e.tipo === 'VITIMA');
      if (primeiraVitima) {
        setVitimaId(primeiraVitima.id);
      }
      const primeiroSuspeito = envs.find((e) => e.tipo === 'SUSPEITO');
      if (primeiroSuspeito) {
        setAgressorId(primeiroSuspeito.id);
      }
    } catch {
      setEnvolvidosOcorrencia([]);
    } finally {
      setCarregandoEnvolvidos(false);
    }
  };

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
      avisar(t('medidas:validacoes.campos_obrigatorios'), 'erro');
      return;
    }
    if (vitimaId.trim() === agressorId.trim()) {
      avisar(t('medidas:validacoes.vitima_igual_agressor'), 'erro');
      return;
    }
    if (restricoesSelecionadas.length === 0) {
      avisar(t('medidas:validacoes.restricao_min'), 'erro');
      return;
    }
    try {
      await medidasService.conceder({
        ocorrencia_id: ocorrenciaId.trim(),
        vitima_id: vitimaId.trim(),
        agressor_id: agressorId.trim(),
        tipos_restricao: restricoesSelecionadas,
        prazo_dias: Number(prazoDias),
        distancia_minima_metros: distanciaMinima ? Number(distanciaMinima) : undefined,
        condicoes_especificas: condicoesEspecificas.trim() || undefined,
      });
      avisar(t('medidas:notificacoes.concedida_sucesso'), 'sucesso');
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
      avisar(t('medidas:validacoes.justificativa_min'), 'erro');
      return;
    }
    try {
      await medidasService.renovar(medidaAlvo.id, {
        dias_adicionais: Number(diasAdicionais),
        justificativa: justificativaRenovacao.trim(),
      });
      avisar(t('medidas:notificacoes.renovada_sucesso'), 'sucesso');
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
      avisar(t('medidas:validacoes.motivo_revogacao_min'), 'erro');
      return;
    }
    try {
      await medidasService.revogar(medidaAlvo.id, {
        motivo: motivoRevogacao.trim(),
      });
      avisar(t('medidas:notificacoes.revogada_sucesso'), 'sucesso');
      setModalRevogarAberto(false);
      carregarMedidas();
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    }
  };

  const badgeDiasRestantes = (dias: number, status: string) => {
    if (status === 'REVOGADA') {
      return (
        <span className="badge badge-REVOGADA">
          {t('medidas:status.REVOGADA')}
        </span>
      );
    }
    if (dias <= 0) {
      return (
        <span style={{ padding: '0.2rem 0.5rem', borderRadius: '4px', background: 'rgba(239, 68, 68, 0.15)', color: 'var(--danger)', fontSize: '0.8rem', fontWeight: 700 }}>
          {t('medidas:vigencia.expirada', { dias: Math.abs(dias) })}
        </span>
      );
    }
    if (dias <= 15) {
      return (
        <span style={{ padding: '0.2rem 0.5rem', borderRadius: '4px', background: 'rgba(245, 158, 11, 0.15)', color: 'var(--warn)', fontSize: '0.8rem', fontWeight: 700 }}>
          ⚠️ {t('medidas:vigencia.dias_restantes', { dias })}
        </span>
      );
    }
    return (
      <span style={{ padding: '0.2rem 0.5rem', borderRadius: '4px', background: 'rgba(16, 185, 129, 0.15)', color: 'var(--ok)', fontSize: '0.8rem', fontWeight: 600 }}>
        {t('medidas:vigencia.dias_restantes', { dias })}
      </span>
    );
  };

  return (
    <div className="medidas-page" style={{ padding: '1.5rem', maxWidth: '1400px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '1.75rem', fontWeight: 700, color: 'var(--ink)' }}>{t('medidas:titulo')}</h1>
          <p style={{ margin: '0.25rem 0 0', color: 'var(--muted)' }}>
            {t('medidas:subtitulo')}
          </p>
        </div>
        {tem('DELEGADO') && (
          <button
            className="btn btn-primary"
            onClick={abrirModalConceder}
            style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.6rem 1.2rem', fontWeight: 600, height: '42px' }}
          >
            <span>+</span> {t('medidas:btn_conceder')}
          </button>
        )}
      </div>

      {/* Barra de Filtros com GlideSelect */}
      <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', marginBottom: '1.25rem', background: 'var(--card)', padding: '0.85rem 1rem', borderRadius: '8px', border: '1px solid var(--line)', flexWrap: 'wrap' }}>
        <div style={{ minWidth: '220px' }}>
          <GlideSelect
            options={opcoesStatusMedidas}
            value={filtroStatus}
            onChange={(val) => setFiltroStatus(val)}
            fullWidth
            ariaLabel={t('medidas:titulo')}
          />
        </div>
        <span style={{ marginLeft: 'auto', alignSelf: 'center', color: 'var(--muted)', fontSize: '0.9rem' }}>
          {t('medidas:total_registrado')}: <strong style={{ color: 'var(--ink)' }}>{total}</strong>
        </span>
      </div>

      {/* Cards de Medidas */}
      {carregando ? (
        <p style={{ textAlign: 'center', padding: '3rem', color: 'var(--muted)' }}>{t('medidas:carregando')}</p>
      ) : medidas.length === 0 ? (
        <p style={{ textAlign: 'center', padding: '3rem', color: 'var(--muted)' }}>{t('medidas:nenhuma_encontrada')}</p>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: '1.25rem' }}>
          {medidas.map((m) => (
            <div
              key={m.id}
              style={{
                background: 'var(--card)',
                borderRadius: '8px',
                border: '1px solid var(--line)',
                padding: '1.25rem',
                display: 'flex',
                flexDirection: 'column',
                boxShadow: 'var(--shadow-card)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                <span style={{ fontWeight: 700, fontSize: '1.1rem', color: 'var(--primary)' }}>{m.numero_referencia}</span>
                {badgeDiasRestantes(m.dias_restantes, m.status)}
              </div>

              <div style={{ fontSize: '0.85rem', color: 'var(--muted)', marginBottom: '0.75rem', lineHeight: 1.6 }}>
                <div>{t('medidas:card.ocorrencia')}: <strong style={{ color: 'var(--ink)' }}>{m.ocorrencia_id.substring(0, 8)}...</strong></div>
                <div>{t('medidas:card.inicio')}: <strong style={{ color: 'var(--ink)' }}>{m.data_inicio}</strong> &bull; {t('medidas:card.vencimento')}: <strong style={{ color: 'var(--ink)' }}>{m.data_vencimento}</strong></div>
                {m.distancia_minima_metros && (
                  <div>{t('medidas:card.distancia_minima')}: <strong style={{ color: 'var(--danger)' }}>{m.distancia_minima_metros} {t('medidas:card.metros')}</strong></div>
                )}
              </div>

              {/* Tags de Restrição */}
              <div style={{ marginBottom: '1rem', display: 'flex', flexWrap: 'wrap', gap: '0.35rem' }}>
                {m.tipos_restricao.map((tKey) => (
                  <span
                    key={tKey}
                    style={{
                      fontSize: '0.75rem',
                      padding: '0.2rem 0.5rem',
                      borderRadius: '4px',
                      background: 'var(--card-hover)',
                      border: '1px solid var(--line)',
                      color: 'var(--ink)',
                    }}
                  >
                    {t(`medidas:restricoes.${tKey}`, { defaultValue: tKey.replace(/_/g, ' ') })}
                  </span>
                ))}
              </div>

              {m.condicoes_especificas && (
                <div style={{ fontSize: '0.8rem', background: 'var(--card-hover)', borderLeft: '3px solid var(--primary)', padding: '0.5rem', borderRadius: '4px', marginBottom: '1rem', color: 'var(--ink)' }}>
                  <em>"{m.condicoes_especificas}"</em>
                </div>
              )}

              {/* Rodapé e Ações do Delegado */}
              <div style={{ marginTop: 'auto', borderTop: '1px solid var(--line)', paddingTop: '0.75rem', display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
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
                      style={{ height: '36px' }}
                    >
                      {t('medidas:acoes.renovar')}
                    </button>
                    <button
                      className="btn btn-sm btn-ghost"
                      style={{ color: 'var(--danger)', height: '36px' }}
                      onClick={() => {
                        setMedidaAlvo(m);
                        setMotivoRevogacao('');
                        setModalRevogarAberto(true);
                      }}
                    >
                      {t('medidas:acoes.revogar')}
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
        <div className="modal-backdrop" style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1200 }}>
          <div style={{ background: 'var(--card)', color: 'var(--ink)', padding: '1.5rem', borderRadius: '12px', border: '1px solid var(--line)', maxWidth: '620px', width: '90%', maxHeight: '90vh', overflowY: 'auto', boxShadow: 'var(--shadow-pop)' }}>
            <h2 style={{ marginTop: 0, color: 'var(--ink)' }}>{t('medidas:modal_conceder.titulo')}</h2>
            <p style={{ color: 'var(--muted)', fontSize: '0.9rem', marginTop: '-0.5rem', marginBottom: '1rem' }}>
              {t('medidas:modal_conceder.subtitulo')}
            </p>
            <form onSubmit={executarConcessao}>
              {/* Campo Ocorrência com GlideSelect e Toggle Manual */}
              <div style={{ marginBottom: '1rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                  <label style={{ fontWeight: 600, color: 'var(--ink)', margin: 0, fontSize: '0.88rem' }}>
                    {t('medidas:modal_conceder.campo_ocorrencia')}
                  </label>
                  {listaOcorrencias.length > 0 && (
                    <button
                      type="button"
                      className="btn btn-sm btn-link"
                      onClick={() => setModoManualOcorrencia(!modoManualOcorrencia)}
                      style={{ fontSize: '0.75rem', padding: '0 4px', textDecoration: 'underline', color: 'var(--primary)' }}
                    >
                      {modoManualOcorrencia ? t('medidas:modal_conceder.selecionar_da_lista') : t('medidas:modal_conceder.digitar_id_manual')}
                    </button>
                  )}
                </div>

                {!modoManualOcorrencia && listaOcorrencias.length > 0 ? (
                  <GlideSelect
                    options={opcoesOcorrenciasModal}
                    value={ocorrenciaId}
                    onChange={(val) => selecionarOuCarregarOcorrencia(val)}
                    placeholder={t('medidas:modal_conceder.selecionar_ocorrencia')}
                    fullWidth
                    menuWidth="100%"
                    ariaLabel={t('medidas:modal_conceder.campo_ocorrencia')}
                  />
                ) : (
                  <input
                    type="text"
                    className="form-control"
                    value={ocorrenciaId}
                    onChange={(e) => selecionarOuCarregarOcorrencia(e.target.value)}
                    placeholder={t('medidas:modal_conceder.placeholder_ocorrencia')}
                    style={{ width: '100%', height: '42px', padding: '0.6rem 0.8rem', background: 'var(--bg)', color: 'var(--ink)', border: '1px solid var(--line)', borderRadius: '8px' }}
                    required
                  />
                )}
                {carregandoEnvolvidos && (
                  <small style={{ color: 'var(--muted)', fontSize: '0.75rem', marginTop: '0.25rem', display: 'block' }}>
                    {t('medidas:modal_conceder.carregando_envolvidos')}
                  </small>
                )}
              </div>

              {/* Campos Vítima e Agressor com GlideSelect Inteligente */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                    <label style={{ fontWeight: 600, color: 'var(--ink)', margin: 0, fontSize: '0.85rem' }}>
                      {t('medidas:modal_conceder.campo_vitima')}
                    </label>
                    {envolvidosOcorrencia.length > 0 && (
                      <button
                        type="button"
                        className="btn btn-sm btn-link"
                        onClick={() => setModoManualVitima(!modoManualVitima)}
                        style={{ fontSize: '0.72rem', padding: '0 2px', textDecoration: 'underline', color: 'var(--primary)' }}
                      >
                        {modoManualVitima ? t('medidas:modal_conceder.selecionar_da_lista') : t('medidas:modal_conceder.digitar_id_manual')}
                      </button>
                    )}
                  </div>

                  {!modoManualVitima && envolvidosOcorrencia.length > 0 ? (
                    <GlideSelect
                      options={opcoesVitimasModal}
                      value={vitimaId}
                      onChange={(val) => setVitimaId(val)}
                      placeholder={t('medidas:modal_conceder.selecionar_vitima')}
                      fullWidth
                      menuWidth="100%"
                      ariaLabel={t('medidas:modal_conceder.campo_vitima')}
                    />
                  ) : (
                    <input
                      type="text"
                      className="form-control"
                      value={vitimaId}
                      onChange={(e) => setVitimaId(e.target.value)}
                      placeholder={t('medidas:modal_conceder.placeholder_vitima')}
                      style={{ width: '100%', height: '42px', padding: '0.6rem 0.8rem', background: 'var(--bg)', color: 'var(--ink)', border: '1px solid var(--line)', borderRadius: '8px' }}
                      required
                    />
                  )}
                </div>

                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                    <label style={{ fontWeight: 600, color: 'var(--ink)', margin: 0, fontSize: '0.85rem' }}>
                      {t('medidas:modal_conceder.campo_agressor')}
                    </label>
                    {envolvidosOcorrencia.length > 0 && (
                      <button
                        type="button"
                        className="btn btn-sm btn-link"
                        onClick={() => setModoManualAgressor(!modoManualAgressor)}
                        style={{ fontSize: '0.72rem', padding: '0 2px', textDecoration: 'underline', color: 'var(--primary)' }}
                      >
                        {modoManualAgressor ? t('medidas:modal_conceder.selecionar_da_lista') : t('medidas:modal_conceder.digitar_id_manual')}
                      </button>
                    )}
                  </div>

                  {!modoManualAgressor && envolvidosOcorrencia.length > 0 ? (
                    <GlideSelect
                      options={opcoesAgressoresModal}
                      value={agressorId}
                      onChange={(val) => setAgressorId(val)}
                      placeholder={t('medidas:modal_conceder.selecionar_agressor')}
                      fullWidth
                      menuWidth="100%"
                      ariaLabel={t('medidas:modal_conceder.campo_agressor')}
                    />
                  ) : (
                    <input
                      type="text"
                      className="form-control"
                      value={agressorId}
                      onChange={(e) => setAgressorId(e.target.value)}
                      placeholder={t('medidas:modal_conceder.placeholder_agressor')}
                      style={{ width: '100%', height: '42px', padding: '0.6rem 0.8rem', background: 'var(--bg)', color: 'var(--ink)', border: '1px solid var(--line)', borderRadius: '8px' }}
                      required
                    />
                  )}
                </div>
              </div>

              {/* Seletor de Restrições em Checkbox com SpringCheck */}
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontWeight: 600, marginBottom: '0.35rem', color: 'var(--ink)' }}>
                  {t('medidas:modal_conceder.campo_restricoes')}
                </label>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', background: 'var(--bg)', padding: '10px', borderRadius: '8px', border: '1px solid var(--line)' }}>
                  {TIPOS_RESTRICAO_CHAVES.map((optKey) => {
                    const isChecked = restricoesSelecionadas.includes(optKey);
                    return (
                      <div
                        key={optKey}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          minHeight: '40px',
                          padding: '0 10px',
                          borderRadius: '6px',
                          background: isChecked ? 'var(--card-hover)' : 'transparent',
                          border: isChecked ? '1px solid var(--primary)' : '1px solid transparent',
                          transition: 'all 0.15s ease',
                          cursor: 'pointer',
                        }}
                        onClick={() => {
                          if (isChecked) {
                            setRestricoesSelecionadas(restricoesSelecionadas.filter((id) => id !== optKey));
                          } else {
                            setRestricoesSelecionadas([...restricoesSelecionadas, optKey]);
                          }
                        }}
                      >
                        <SpringCheck
                          checked={isChecked}
                          strike="none"
                          label={t(`medidas:restricoes.${optKey}`, { defaultValue: optKey.replace(/_/g, ' ') })}
                          onChange={(checked) => {
                            if (checked) {
                              if (!restricoesSelecionadas.includes(optKey)) setRestricoesSelecionadas([...restricoesSelecionadas, optKey]);
                            } else {
                              setRestricoesSelecionadas(restricoesSelecionadas.filter((id) => id !== optKey));
                            }
                          }}
                        />
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Prazos e Distâncias Alinhados na Mesma Altura */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem', alignItems: 'end' }}>
                <div style={{ display: 'flex', flexDirection: 'column', height: '100%', justifyContent: 'space-between' }}>
                  <label style={{ display: 'flex', alignItems: 'flex-end', fontWeight: 600, marginBottom: '0.35rem', color: 'var(--ink)', fontSize: '0.85rem', minHeight: '2.5rem' }}>
                    {t('medidas:modal_conceder.campo_prazo')}
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="730"
                    value={prazoDias}
                    onChange={(e) => setPrazoDias(Number(e.target.value))}
                    style={{ width: '100%', height: '42px', padding: '0.6rem 0.8rem', background: 'var(--bg)', color: 'var(--ink)', border: '1px solid var(--line)', borderRadius: '8px' }}
                    required
                  />
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', height: '100%', justifyContent: 'space-between' }}>
                  <label style={{ display: 'flex', alignItems: 'flex-end', fontWeight: 600, marginBottom: '0.35rem', color: 'var(--ink)', fontSize: '0.85rem', minHeight: '2.5rem' }}>
                    {t('medidas:modal_conceder.campo_distancia')}
                  </label>
                  <input
                    type="number"
                    min="10"
                    max="50000"
                    value={distanciaMinima}
                    onChange={(e) => setDistanciaMinima(Number(e.target.value))}
                    style={{ width: '100%', height: '42px', padding: '0.6rem 0.8rem', background: 'var(--bg)', color: 'var(--ink)', border: '1px solid var(--line)', borderRadius: '8px' }}
                  />
                </div>
              </div>

              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', fontWeight: 600, marginBottom: '0.35rem', color: 'var(--ink)' }}>
                  {t('medidas:modal_conceder.campo_condicoes')}
                </label>
                <textarea
                  className="form-control"
                  rows={3}
                  value={condicoesEspecificas}
                  onChange={(e) => setCondicoesEspecificas(e.target.value)}
                  placeholder={t('medidas:modal_conceder.placeholder_condicoes')}
                  style={{ width: '100%', padding: '0.6rem 0.8rem', background: 'var(--bg)', color: 'var(--ink)', border: '1px solid var(--line)', borderRadius: '8px' }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
                <button type="button" className="btn btn-ghost" onClick={() => setModalConcederAberto(false)} style={{ height: '42px' }}>{t('medidas:acoes.cancelar')}</button>
                <button type="submit" className="btn btn-primary" style={{ height: '42px' }}>{t('medidas:modal_conceder.btn_submit')}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal Renovar */}
      {modalRenovarAberto && medidaAlvo && (
        <div className="modal-backdrop" style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1200 }}>
          <div style={{ background: 'var(--card)', color: 'var(--ink)', padding: '1.5rem', borderRadius: '12px', border: '1px solid var(--line)', maxWidth: '500px', width: '90%', boxShadow: 'var(--shadow-pop)' }}>
            <h2 style={{ marginTop: 0, color: 'var(--ink)' }}>{t('medidas:modal_renovar.titulo')} — {medidaAlvo.numero_referencia}</h2>
            <p style={{ color: 'var(--muted)', fontSize: '0.9rem', marginTop: '-0.5rem', marginBottom: '1rem' }}>
              {t('medidas:modal_renovar.subtitulo')}
            </p>
            <form onSubmit={executarRenovacao}>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontWeight: 600, marginBottom: '0.35rem', color: 'var(--ink)' }}>
                  {t('medidas:modal_renovar.campo_dias')}
                </label>
                <input
                  type="number"
                  min="1"
                  max="365"
                  value={diasAdicionais}
                  onChange={(e) => setDiasAdicionais(Number(e.target.value))}
                  style={{ width: '100%', height: '42px', padding: '0.6rem 0.8rem', background: 'var(--bg)', color: 'var(--ink)', border: '1px solid var(--line)', borderRadius: '8px' }}
                  required
                />
              </div>

              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', fontWeight: 600, marginBottom: '0.35rem', color: 'var(--ink)' }}>
                  {t('medidas:modal_renovar.campo_justificativa')}
                </label>
                <textarea
                  className="form-control"
                  rows={4}
                  value={justificativaRenovacao}
                  onChange={(e) => setJustificativaRenovacao(e.target.value)}
                  placeholder={t('medidas:modal_renovar.placeholder_justificativa')}
                  style={{ width: '100%', padding: '0.6rem 0.8rem', background: 'var(--bg)', color: 'var(--ink)', border: '1px solid var(--line)', borderRadius: '8px' }}
                  required
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
                <button type="button" className="btn btn-ghost" onClick={() => setModalRenovarAberto(false)} style={{ height: '42px' }}>{t('medidas:acoes.cancelar')}</button>
                <button type="submit" className="btn btn-primary" style={{ height: '42px' }}>{t('medidas:modal_renovar.btn_submit')}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal Revogar */}
      {modalRevogarAberto && medidaAlvo && (
        <div className="modal-backdrop" style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1200 }}>
          <div style={{ background: 'var(--card)', color: 'var(--ink)', padding: '1.5rem', borderRadius: '12px', border: '1px solid var(--line)', maxWidth: '500px', width: '90%', boxShadow: 'var(--shadow-pop)' }}>
            <h2 style={{ marginTop: 0, color: 'var(--danger)' }}>{t('medidas:modal_revogar.titulo')} — {medidaAlvo.numero_referencia}</h2>
            <p style={{ color: 'var(--muted)', fontSize: '0.9rem', marginTop: '-0.5rem', marginBottom: '1rem' }}>
              {t('medidas:modal_revogar.subtitulo')}
            </p>
            <form onSubmit={executarRevogacao}>
              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', fontWeight: 600, marginBottom: '0.35rem', color: 'var(--ink)' }}>
                  {t('medidas:modal_revogar.campo_motivo')}
                </label>
                <textarea
                  className="form-control"
                  rows={4}
                  value={motivoRevogacao}
                  onChange={(e) => setMotivoRevogacao(e.target.value)}
                  placeholder={t('medidas:modal_revogar.placeholder_motivo')}
                  style={{ width: '100%', padding: '0.6rem 0.8rem', background: 'var(--bg)', color: 'var(--ink)', border: '1px solid var(--line)', borderRadius: '8px' }}
                  required
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
                <button type="button" className="btn btn-ghost" onClick={() => setModalRevogarAberto(false)} style={{ height: '42px' }}>{t('medidas:acoes.cancelar')}</button>
                <button type="submit" className="btn btn-danger" style={{ height: '42px' }}>{t('medidas:modal_revogar.btn_submit')}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default MedidasProtetivasPage;
