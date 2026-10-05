import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { MapaTatico } from '../components/painel/MapaTatico';
import { PrioridadeBadge } from '../components/PrioridadeBadge';
import { StatusBadge } from '../components/StatusBadge';
import { useAuth } from '../hooks/useAuth';
import { useTempoReal } from '../hooks/useTempoReal';
import { useToast } from '../hooks/useToast';
import { mensagemDeErro } from '../services/api';
import { despachoService } from '../services/despachoService';
import { ocorrenciasService } from '../services/ocorrenciasService';
import { viaturasService } from '../services/viaturasService';
import {
  LIMIAR_CRITICIDADE_24H,
  PERIODOS_MANCHA_DIAS,
  PERIODO_MANCHA_PADRAO_DIAS,
  filtrarPontosMancha,
  idadeEmMinutos,
  listarCriticas24h,
  listarEmAberto,
  listarNaturezas,
  resumirPorNatureza,
} from '../utils/manchas';
import type { EventoTempoReal, NivelCriticidade, OcorrenciaResumo, OrdemDespacho, Papel, StatusSimuladorCompleto, Sugestoes, Viatura } from '../types/api';
import { NIVEIS_CRITICIDADE, PAPEIS_DESTINATARIOS_ALERTA } from '../types/api';
import { formatarHora } from '../utils/datas';
import { inteligenciaService, type AreaRisco } from '../services/inteligenciaService';
import { GlideSelect, type GlideSelectOption } from '../components/common/GlideSelect';

/**
 * Painel tático (RF02 / RNF01): carga inicial por REST, atualizações por WebSocket,
 * fallback tabular quando não há sinal (RNF04*), sugestão + despacho + encerramento.
 */
export const PainelTaticoPage: React.FC = () => {
  const { t } = useTranslation(['painel', 'common']);
  const { avisar } = useToast();
  const { tem } = useAuth();
  const podeDespachar = tem('OPERADOR_CENTRAL', 'SUPERVISOR');
  const podeEmitirAlerta = tem('OPERADOR_CENTRAL', 'SUPERVISOR', 'DELEGADO');
  const [viaturas, setViaturas] = useState<Viatura[]>([]);
  const [ocorrencias, setOcorrencias] = useState<OcorrenciaResumo[]>([]);
  const [ordens, setOrdens] = useState<OrdemDespacho[]>([]);
  const [selecionada, setSelecionada] = useState<string | null>(null);
  const [sugestoes, setSugestoes] = useState<Sugestoes | null>(null);
  const [simulador, setSimulador] = useState<StatusSimuladorCompleto | null>(null);
  const [desfecho, setDesfecho] = useState('');
  const [ocupado, setOcupado] = useState(false);
  const [ultimoEvento, setUltimoEvento] = useState<string>('');
  const [heatAtivo, setHeatAtivo] = useState(false);
  const [periodoDias, setPeriodoDias] = useState<number>(PERIODO_MANCHA_PADRAO_DIAS);
  const [naturezaFiltro, setNaturezaFiltro] = useState('');
  const [detalhesCriticos, setDetalhesCriticos] = useState(false);
  // comunicados operacionais (chegada ao local etc.) — ficam listados, não só no toast
  const [comunicados, setComunicados] = useState<{ id: string; em: string; texto: string }[]>([]);

  // RF05 / UC11: Áreas de risco dinâmicas e emissão de alertas de criticidade
  const [areasRisco, setAreasRisco] = useState<AreaRisco[]>([]);
  const [areasRiscoAtivo, setAreasRiscoAtivo] = useState(true);
  const [modalAlertaAberto, setModalAlertaAberto] = useState(false);
  const [areaSelecionadaParaAlerta, setAreaSelecionadaParaAlerta] = useState('');
  const [alertaTitulo, setAlertaTitulo] = useState('Alerta Tático de Criticidade');
  const [alertaMensagem, setAlertaMensagem] = useState('');
  const [alertaCriticidade, setAlertaCriticidade] = useState<NivelCriticidade>('CRITICA');
  const [alertaPapelDestinatario, setAlertaPapelDestinatario] = useState<Papel | ''>('');
  const [enviandoAlerta, setEnviandoAlerta] = useState(false);

  const opcoesAreaRisco: GlideSelectOption[] = useMemo(() => [
    { value: '', label: t('painel:alerta.nenhuma_area') },
    ...areasRisco.map((a) => ({
      value: a.id,
      label: t('painel:alerta.opcao_area', { nome: a.nome, nivel: a.nivel_risco, total: a.total_ocorrencias }),
      tag: a.nivel_risco,
    })),
  ], [areasRisco, t]);

  const opcoesCriticidade: GlideSelectOption[] = useMemo(
    () => NIVEIS_CRITICIDADE.map((n) => ({ value: n, label: t(`painel:alerta.criticidade.${n}`) })),
    [t],
  );

  // Derivadas do tipo Papel: um valor que não existe no backend não chega a ser oferecido (N3).
  const opcoesDestinatarios: GlideSelectOption[] = useMemo(() => [
    { value: '', label: t('painel:alerta.destinatario_todos') },
    ...PAPEIS_DESTINATARIOS_ALERTA.map((p) => ({ value: p, label: t('painel:alerta.destinatario_papel', { papel: t(`common:papel.${p}`) }) })),
  ], [t]);

  const carregar = useCallback(async () => {
    try {
      const [vs, os, ods, sim, areas] = await Promise.all([
        viaturasService.listar(),
        ocorrenciasService.listar(['VALIDADA', 'EM_ATENDIMENTO'], 200, 0, false, undefined, true),
        despachoService.listar(true),
        viaturasService.simulador().catch(() => null),
        inteligenciaService.obterAreasRisco(periodoDias).catch(() => []),
      ]);
      setViaturas(vs);
      setOcorrencias(os.itens);
      setOrdens(ods);
      setSimulador(sim);
      setAreasRisco(areas);
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    }
  }, [avisar, periodoDias]);

  useEffect(() => {
    carregar();
  }, [carregar]);

  // recalcula "sinal" no cliente a cada 5 s para viaturas que pararam de emitir (RNF04*)
  useEffect(() => {
    const id = window.setInterval(() => {
      setViaturas((vs) => vs.map((v) => {
        if (!v.posicao_registrada_em || v.sinal === 'SEM_POSICAO') return v;
        const idade = (Date.now() - new Date(v.posicao_registrada_em).getTime()) / 1000;
        const sinal = idade > 60 ? 'SEM_SINAL' : 'OK';
        return sinal === v.sinal ? v : { ...v, sinal };
      }));
    }, 5000);
    return () => window.clearInterval(id);
  }, []);

  const onEvento = useCallback((e: EventoTempoReal) => {
    const evento = t(`painel:eventos.${e.tipo}`, { defaultValue: t('painel:eventos.desconhecido') });
    setUltimoEvento(t('painel:eventos.ultimo', { evento, hora: formatarHora(e.ocorrido_em) }));
    const d = e.dados as Record<string, string | number | null>;
    const atualizarViatura = () => setViaturas((vs) => vs.map((v) => v.id === d.viatura_id
      ? { ...v, situacao: (d.situacao as Viatura['situacao']) ?? v.situacao, latitude: (d.latitude as number) ?? v.latitude, longitude: (d.longitude as number) ?? v.longitude, posicao_registrada_em: (d.registrada_em as string) ?? v.posicao_registrada_em, sinal: d.latitude != null ? 'OK' : v.sinal }
      : v));
    switch (e.tipo) {
      case 'PosicaoAtualizada':
      case 'ViaturaSituacaoAlterada':
        atualizarViatura();
        break;
      case 'ViaturaChegouAoLocal': {
        // RF18/RF19: a viatura chegou à ocorrência e iniciou os procedimentos de atendimento
        atualizarViatura();
        const texto = t('painel:chegada.mensagem', { prefixo: d.prefixo, protocolo: d.numero_protocolo, ordem: d.numero_ordem });
        avisar(texto, 'sucesso');
        setComunicados((cs) => [{ id: `${d.viatura_id}-${e.ocorrido_em}`, em: e.ocorrido_em, texto }, ...cs].slice(0, 20));
        break;
      }
      case 'OcorrenciaValidada':
        ocorrenciasService.listar(['VALIDADA', 'EM_ATENDIMENTO'], 200, 0, false, undefined, true).then((p) => setOcorrencias(p.itens)).catch(() => undefined);
        break;
      case 'OcorrenciaDespachada':
        setOcorrencias((os) => os.map((o) => (o.ocorrencia_id === d.ocorrencia_id ? { ...o, status: 'EM_ATENDIMENTO' } : o)));
        despachoService.listar(true).then(setOrdens).catch(() => undefined);
        break;
      case 'OcorrenciaEncerrada':
      case 'OcorrenciaArquivada':
      case 'OcorrenciaExcluida':
        setOcorrencias((os) => os.filter((o) => o.ocorrencia_id !== d.ocorrencia_id));
        despachoService.listar(true).then(setOrdens).catch(() => undefined);
        break;
      default:
        break;
    }
  }, [t, avisar]);

  const conexao = useTempoReal(onEvento, carregar);
  const viaturasEmDeslocamento = viaturas.filter((v) => v.situacao === 'EM_DESLOCAMENTO');

  useEffect(() => {
    if (!simulador?.orquestrador?.ligado) return undefined;
    const id = window.setInterval(() => {
      viaturasService.simulador().then(setSimulador).catch(() => undefined);
    }, 5000);
    return () => window.clearInterval(id);
  }, [simulador?.orquestrador?.ligado]);

  const ocorrenciaSel = useMemo(() => ocorrencias.find((o) => o.ocorrencia_id === selecionada) ?? null, [ocorrencias, selecionada]);
  const semSinal = viaturas.filter((v) => v.sinal !== 'OK');
  const naturezas = useMemo(() => listarNaturezas(ocorrencias), [ocorrencias]);
  const pontosCalor = useMemo(
    () => (heatAtivo ? filtrarPontosMancha(ocorrencias, periodoDias, naturezaFiltro) : []),
    [heatAtivo, ocorrencias, periodoDias, naturezaFiltro],
  );
  const criticas = useMemo(
    () => (heatAtivo ? listarCriticas24h(ocorrencias, naturezaFiltro) : []),
    [heatAtivo, ocorrencias, naturezaFiltro],
  );
  const criticidade = criticas.length >= LIMIAR_CRITICIDADE_24H;
  const resumoCriticas = useMemo(() => resumirPorNatureza(criticas).slice(0, 3), [criticas]);
  const emAberto = useMemo(
    () => (heatAtivo ? listarEmAberto(ocorrencias, naturezaFiltro) : []),
    [heatAtivo, ocorrencias, naturezaFiltro],
  );

  const idade = (criadaEm: string): string => {
    const min = idadeEmMinutos(criadaEm);
    if (min < 60) return t('painel:manchas.ha_minutos', { n: min });
    if (min < 24 * 60) return t('painel:manchas.ha_horas', { n: Math.floor(min / 60) });
    return t('painel:manchas.ha_dias', { n: Math.floor(min / (24 * 60)) });
  };

  const selecionar = async (id: string) => {
    setSelecionada(id);
    setSugestoes(null);
    const o = ocorrencias.find((x) => x.ocorrencia_id === id);
    if ((o?.status === 'VALIDADA' || o?.status === 'EM_ATENDIMENTO') && podeDespachar) {
      try {
        setSugestoes(await despachoService.sugestoes(id));
      } catch (err) {
        avisar(mensagemDeErro(err), 'erro');
      }
    }
  };

  const despachar = async (viaturaId: string) => {
    if (!selecionada) return;
    setOcupado(true);
    try {
      const ordem = await despachoService.despachar(selecionada, viaturaId);
      avisar(t('painel:despacho.ok', { numero: ordem.numero }), 'sucesso');
      setSugestoes(null);
      await carregar();
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    } finally {
      setOcupado(false);
    }
  };

  const encerrar = async () => {
    if (!selecionada || !desfecho.trim()) return;
    setOcupado(true);
    try {
      await ocorrenciasService.encerrar(selecionada, desfecho);
      avisar(t('painel:encerrar.ok'), 'sucesso');
      setDesfecho('');
      setSelecionada(null);
      await carregar();
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    } finally {
      setOcupado(false);
    }
  };

  const alternarSimulador = async () => {
    try {
      setSimulador(simulador?.ligado ? await viaturasService.desligarSimulador() : await viaturasService.ligarSimulador());
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    }
  };

  const handleEmitirAlerta = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!alertaTitulo.trim() || !alertaMensagem.trim()) return;
    setEnviandoAlerta(true);
    try {
      const area = areasRisco.find((a) => a.id === areaSelecionadaParaAlerta);
      await inteligenciaService.emitirAlertaCriticidade({
        titulo: alertaTitulo,
        mensagem: alertaMensagem,
        nivel_criticidade: alertaCriticidade,
        area_risco_id: area?.id,
        latitude: area?.latitude,
        longitude: area?.longitude,
        raio_metros: area?.raio_metros,
        papel_destinatario: alertaPapelDestinatario || undefined,
      });
      avisar(t('painel:alerta.sucesso'), 'sucesso');
      setModalAlertaAberto(false);
      setAlertaMensagem('');
      setAlertaPapelDestinatario('');
      setAreaSelecionadaParaAlerta('');
      await carregar();
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    } finally {
      setEnviandoAlerta(false);
    }
  };

  return (
    <div className="painel">
      <div className="painel-barra">
        <span className={`conexao conexao-${conexao}`}>● {t(`painel:conexao.${conexao}`)}</span>
        <span className="muted small">{ultimoEvento}</span>
        <span className="espaco" />
        {podeDespachar && simulador && (
          <button className={`btn ${simulador.ligado ? 'btn-warn' : 'btn-primary'}`} onClick={alternarSimulador}>
            {simulador.ligado ? t('painel:simulador.desligar') : t('painel:simulador.ligar')} ({simulador.ticks})
          </button>
        )}
        {podeDespachar && simulador?.orquestrador?.ligado && (
          <span className="badge badge-OK">
            {t('painel:simulador.despacho_auto')} · {t('painel:simulador.despacho_contador', { despachados: simulador.orquestrador.despachados, encerrados: simulador.orquestrador.encerrados })}
          </span>
        )}
        <button
          type="button"
          className={`btn ${areasRiscoAtivo ? 'btn-warn' : 'btn-ghost'}`}
          onClick={() => setAreasRiscoAtivo((v) => !v)}
          title="Exibir manchas criminais e áreas de risco calculadas"
        >
          🚨 {areasRiscoAtivo ? t('painel:areas_risco.ocultar') : t('painel:areas_risco.mostrar')} ({areasRisco.length})
        </button>
        {podeEmitirAlerta && (
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => {
              setAreaSelecionadaParaAlerta('');
              setAlertaTitulo('Alerta Tático de Criticidade');
              setAlertaMensagem('');
              setModalAlertaAberto(true);
            }}
            title="Emitir alerta de criticidade operacional em tempo real"
          >
            📢 {t('painel:alerta.emitir')}
          </button>
        )}
        <button className={`btn ${heatAtivo ? 'btn-warn' : 'btn-ghost'}`} onClick={() => setHeatAtivo((v) => !v)}>
          {heatAtivo ? t('painel:manchas.ocultar') : t('painel:manchas.mostrar')}
        </button>
        {heatAtivo && (
          <>
            <label className="muted small">
              {t('painel:manchas.periodo')}
              <select value={periodoDias} onChange={(e) => setPeriodoDias(Number(e.target.value))}>
                {PERIODOS_MANCHA_DIAS.map((d) => (
                  <option key={d} value={d}>{t('painel:manchas.dias', { n: d })}</option>
                ))}
              </select>
            </label>
            <label className="muted small">
              {t('painel:manchas.natureza')}
              <select value={naturezaFiltro} onChange={(e) => setNaturezaFiltro(e.target.value)}>
                <option value="">{t('painel:manchas.todas')}</option>
                {naturezas.map((n) => (
                  <option key={n} value={n}>{n}</option>
                ))}
              </select>
            </label>
          </>
        )}
      </div>

      <div className="kpi-grid">
        <div className="kpi-card">
          <span className="kpi-label">{t('painel:kpi.ativas')}</span>
          <span className="kpi-val">{ocorrencias.length}</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-label">{t('painel:kpi.em_atendimento')}</span>
          <span className="kpi-val" style={{ color: 'var(--primary)' }}>
            {ocorrencias.filter((o) => o.status === 'EM_ATENDIMENTO').length}
          </span>
        </div>
        <div className="kpi-card">
          <span className="kpi-label">{t('painel:frota.titulo')}</span>
          <span className="kpi-val">{viaturas.length}</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-label">{t('painel:kpi.sem_sinal')}</span>
          <span className="kpi-val" style={{ color: semSinal.length > 0 ? 'var(--warn)' : 'var(--ok)' }}>
            {semSinal.length}
          </span>
        </div>
      </div>

      <div className="painel-grid">
        <div className="painel-mapa">
          {criticidade && (
            <div className="alerta erro">
              <div>{t('painel:manchas.criticidade', { n: LIMIAR_CRITICIDADE_24H })}</div>
              <div className="criticas-resumo">
                <span>
                  {t('painel:manchas.resumo_24h', { total: criticas.length })}
                  {' · '}
                  {resumoCriticas.map((r) => `${r.natureza} (${r.quantidade})`).join(', ')}
                </span>
                <button className="btn btn-sm btn-ghost" onClick={() => setDetalhesCriticos((v) => !v)}>
                  {detalhesCriticos ? t('painel:manchas.detalhes_ocultar') : t('painel:manchas.detalhes_mostrar')}
                </button>
              </div>
              {detalhesCriticos && (
                <div className="criticas-detalhes">
                  {criticas.map((o) => (
                    <button key={o.ocorrencia_id} className="btn btn-sm btn-ghost" onClick={() => selecionar(o.ocorrencia_id)} title={o.localizacao}>
                      {o.numero_protocolo} · {o.natureza}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
          <MapaTatico
            viaturas={viaturas}
            ocorrencias={ocorrencias}
            ordens={ordens}
            selecionada={selecionada}
            onSelecionarOcorrencia={selecionar}
            heatAtivo={heatAtivo}
            pontosCalor={pontosCalor}
            areasRisco={areasRiscoAtivo ? areasRisco : []}
          />
          {semSinal.length > 0 && (
            <div className="alerta aviso">
              ⚠ {t('painel:sem_sinal.alerta', { n: semSinal.length })}
              <table className="tabela compacta">
                <thead><tr><th>{t('painel:viatura')}</th><th>{t('painel:situacao')}</th><th>{t('painel:ultima_posicao')}</th></tr></thead>
                <tbody>
                  {semSinal.map((v) => (
                    <tr key={v.id}>
                      <td>{v.prefixo}</td>
                      <td><StatusBadge status={v.situacao} grupo="situacao" /></td>
                      <td>{v.latitude !== null ? `${v.latitude.toFixed(4)}, ${v.longitude?.toFixed(4)} · ${formatarHora(v.posicao_registrada_em!)}` : t('painel:sem_sinal.nunca')}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <aside className="painel-lateral">
          {(comunicados.length > 0 || viaturasEmDeslocamento.length > 0) && (
            <section className="card comunicados">
              <h3>{t('painel:chegada.titulo')}</h3>
              {viaturasEmDeslocamento.length > 0 && (
                <p className="muted small">
                  {t('painel:chegada.a_caminho', { n: viaturasEmDeslocamento.length, prefixos: viaturasEmDeslocamento.map((v) => v.prefixo).join(', ') })}
                </p>
              )}
              <ul className="lista">
                {comunicados.map((c) => (
                  <li key={c.id}><span>🚓 {c.texto}<br /><small className="muted">{formatarHora(c.em)}</small></span></li>
                ))}
              </ul>
            </section>
          )}
          <section className="card">
            <h3>{t('painel:ocorrencias.titulo')} <span className="muted">({ocorrencias.length})</span></h3>
            {ocorrencias.length === 0 && <p className="muted">{t('painel:ocorrencias.vazio')}</p>}
            <ul className="lista clicavel">
              {ocorrencias.map((o) => (
                <li key={o.ocorrencia_id} className={o.ocorrencia_id === selecionada ? 'ativo' : ''} onClick={() => selecionar(o.ocorrencia_id)}>
                  <span><strong>{o.numero_protocolo}</strong> · {o.natureza}<br /><small className="muted">{o.localizacao}</small></span>
                  <span className="lista-badges"><StatusBadge status={o.status} /><PrioridadeBadge prioridade={o.prioridade} /></span>
                </li>
              ))}
            </ul>
          </section>

          {heatAtivo && (
            <section className="card">
              <h3>{t('painel:manchas.em_aberto_titulo')} <span className="muted">({emAberto.length})</span></h3>
              {emAberto.length === 0 && <p className="muted">{t('painel:manchas.em_aberto_vazio')}</p>}
              <ul className="lista clicavel">
                {emAberto.map((o) => (
                  <li key={o.ocorrencia_id} className={o.ocorrencia_id === selecionada ? 'ativo' : ''} onClick={() => selecionar(o.ocorrencia_id)}>
                    <span><strong>{o.numero_protocolo}</strong> · {o.natureza}<br /><small className="muted">{idade(o.criada_em)}</small></span>
                    <span className="lista-badges"><StatusBadge status={o.status} /><PrioridadeBadge prioridade={o.prioridade} /></span>
                  </li>
                ))}
              </ul>
            </section>
          )}

          {(ocorrenciaSel?.status === 'VALIDADA' || ocorrenciaSel?.status === 'EM_ATENDIMENTO') && podeDespachar && (
            <section className="card">
              <h3>
                {t(
                  ocorrenciaSel.status === 'EM_ATENDIMENTO' ? 'painel:despacho.titulo_apoio' : 'painel:despacho.titulo',
                  { protocolo: ocorrenciaSel.numero_protocolo },
                )}
              </h3>
              {!sugestoes && <p className="muted">{t('common:actions.loading')}</p>}
              {sugestoes && sugestoes.sugestoes.length > 0 && (
                <ul className="lista">
                  {sugestoes.sugestoes.map((s, i) => (
                    <li key={s.viatura.id}>
                      <span>#{i + 1} <strong>{s.viatura.prefixo}</strong> · {s.distancia_km.toFixed(2)} km</span>
                      <button className="btn btn-primary btn-sm" disabled={ocupado} onClick={() => despachar(s.viatura.id)}>
                        {t(ocorrenciaSel.status === 'EM_ATENDIMENTO' ? 'painel:despacho.despachar_apoio' : 'painel:despacho.despachar')}
                      </button>
                    </li>
                  ))}
                </ul>
              )}
              {sugestoes?.sem_elegiveis && (
                <>
                  <p className="alerta aviso">{t('painel:despacho.sem_elegiveis')}</p>
                  <ul className="lista">
                    {sugestoes.disponiveis_sem_posicao.map((v) => (
                      <li key={v.id}>
                        <span><strong>{v.prefixo}</strong> · <StatusBadge status={v.sinal} grupo="sinal" /></span>
                        <button className="btn btn-sm" disabled={ocupado} onClick={() => despachar(v.id)}>{t('painel:despacho.manual')}</button>
                      </li>
                    ))}
                  </ul>
                </>
              )}
            </section>
          )}

          {ocorrenciaSel && ocorrenciaSel.status === 'EM_ATENDIMENTO' && (
            <section className="card">
              <h3>{t('painel:encerrar.titulo', { protocolo: ocorrenciaSel.numero_protocolo })}</h3>
              <ul className="lista">
                {ordens.filter((o) => o.ocorrencia_id === ocorrenciaSel.ocorrencia_id).map((o) => (
                  <li key={o.id}>
                    <span>
                      <strong>{o.numero}</strong> · {viaturas.find((v) => v.id === o.viatura_id)?.prefixo} · {formatarHora(o.criada_em)}{' '}
                      <span className={`badge ${o.apoio ? 'badge-EM_ATENDIMENTO' : 'badge-OK'}`}>
                        {t(o.apoio ? 'painel:despacho.ordem_apoio' : 'painel:despacho.ordem_principal')}
                      </span>
                    </span>
                  </li>
                ))}
              </ul>
              <label>
                {t('painel:encerrar.desfecho')}
                <textarea rows={2} value={desfecho} onChange={(e) => setDesfecho(e.target.value)} />
              </label>
              <button className="btn btn-danger" disabled={ocupado || !desfecho.trim()} onClick={encerrar}>{t('painel:encerrar.botao')}</button>
            </section>
          )}

          <section className="card">
            <h3>{t('painel:frota.titulo')} <span className="muted">({viaturas.length})</span></h3>
            <table className="tabela compacta">
              <tbody>
                {viaturas.map((v) => (
                  <tr key={v.id}>
                    <td><strong>{v.prefixo}</strong></td>
                    <td><StatusBadge status={v.situacao} grupo="situacao" /></td>
                    <td><StatusBadge status={v.sinal} grupo="sinal" /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        </aside>
      </div>

      {modalAlertaAberto && (
        <div
          className="modal-backdrop"
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0, 0, 0, 0.65)',
            backdropFilter: 'blur(6px)',
            WebkitBackdropFilter: 'blur(6px)',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            zIndex: 2000,
            padding: '1.25rem',
          }}
          onClick={() => setModalAlertaAberto(false)}
        >
          <div
            className="modal-box"
            onClick={(e) => e.stopPropagation()}
            style={{
              maxWidth: 560,
              width: '100%',
              background: 'var(--card)',
              border: '1px solid var(--line)',
              borderRadius: '14px',
              padding: '1.5rem',
              boxShadow: 'var(--shadow-pop)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
              <div>
                <h3 style={{ margin: 0, fontSize: '1.2rem', display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span>📢</span> {t('painel:alerta.titulo_modal')}
                </h3>
                <p className="muted small" style={{ margin: '4px 0 0' }}>
                  {t('painel:alerta.descricao_modal')}
                </p>
              </div>
              <button
                type="button"
                className="btn btn-ghost"
                onClick={() => setModalAlertaAberto(false)}
                style={{ padding: '4px 8px', fontSize: '1.1rem', lineHeight: 1 }}
                aria-label={t('common:actions.fechar', 'Fechar')}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleEmitirAlerta} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div>
                <label style={{ display: 'block', marginBottom: 6, fontWeight: 600, fontSize: '0.88rem' }}>
                  {t('painel:alerta.area_vinculada')}
                </label>
                <GlideSelect
                  options={opcoesAreaRisco}
                  value={areaSelecionadaParaAlerta}
                  onChange={(id) => {
                    setAreaSelecionadaParaAlerta(id);
                    const sel = areasRisco.find((a) => a.id === id);
                    if (sel) {
                      setAlertaTitulo(`Alerta Tático: ${sel.nome}`);
                      setAlertaMensagem(
                        `Atenção ao aumento de ocorrências (${sel.naturezas_predominantes.slice(0, 2).join(', ')}) na área de ${sel.nome}. Reforço de patrulhamento recomendado.`,
                      );
                    }
                  }}
                  fullWidth
                  placeholder={t('painel:alerta.nenhuma_area')}
                />
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: 6, fontWeight: 600, fontSize: '0.88rem' }}>
                  {t('painel:alerta.campo_titulo')}
                </label>
                <input
                  type="text"
                  required
                  value={alertaTitulo}
                  onChange={(e) => setAlertaTitulo(e.target.value)}
                  className="input-text"
                  style={{ width: '100%', boxSizing: 'border-box' }}
                  placeholder="Ex: Alerta de Patrulhamento Reforçado"
                />
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: 6, fontWeight: 600, fontSize: '0.88rem' }}>
                  {t('painel:alerta.campo_criticidade')}
                </label>
                <GlideSelect
                  options={opcoesCriticidade}
                  value={alertaCriticidade}
                  onChange={(val) => setAlertaCriticidade(val as NivelCriticidade)}
                  fullWidth
                />
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: 6, fontWeight: 600, fontSize: '0.88rem' }}>
                  {t('painel:alerta.campo_destinatario')}
                </label>
                <GlideSelect
                  options={opcoesDestinatarios}
                  value={alertaPapelDestinatario}
                  onChange={(val) => setAlertaPapelDestinatario(val as Papel | '')}
                  fullWidth
                />
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: 6, fontWeight: 600, fontSize: '0.88rem' }}>
                  {t('painel:alerta.campo_mensagem')}
                </label>
                <textarea
                  required
                  rows={4}
                  value={alertaMensagem}
                  onChange={(e) => setAlertaMensagem(e.target.value)}
                  className="input-text"
                  style={{ width: '100%', boxSizing: 'border-box', resize: 'vertical' }}
                  placeholder="Descreva a situação operacional, cuidados especiais e diretrizes para as equipes de ronda..."
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 8 }}>
                <button type="button" className="btn btn-ghost" onClick={() => setModalAlertaAberto(false)}>
                  {t('actions.cancelar', 'Cancelar')}
                </button>
                <button type="submit" className="btn btn-primary" disabled={enviandoAlerta}>
                  {enviandoAlerta ? t('painel:alerta.difundindo') : t('painel:alerta.difundir')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
