import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { MapaTatico } from '../components/painel/MapaTatico';
import { StatusBadge } from '../components/StatusBadge';
import { useAuth } from '../hooks/useAuth';
import { useTempoReal } from '../hooks/useTempoReal';
import { useToast } from '../hooks/useToast';
import { mensagemDeErro } from '../services/api';
import { despachoService } from '../services/despachoService';
import { ocorrenciasService } from '../services/ocorrenciasService';
import { viaturasService } from '../services/viaturasService';
import type { EventoTempoReal, OcorrenciaResumo, OrdemDespacho, StatusSimulador, Sugestoes, Viatura } from '../types/api';

/**
 * Painel tático (RF17/RF18/RF19): carga inicial por REST, atualizações por WebSocket,
 * fallback tabular quando não há sinal (RNF04*), sugestão + despacho + encerramento.
 */
export const PainelTaticoPage: React.FC = () => {
  const { t } = useTranslation(['painel', 'common']);
  const { avisar } = useToast();
  const { tem } = useAuth();
  const podeDespachar = tem('OPERADOR_CENTRAL', 'SUPERVISOR');
  const [viaturas, setViaturas] = useState<Viatura[]>([]);
  const [ocorrencias, setOcorrencias] = useState<OcorrenciaResumo[]>([]);
  const [ordens, setOrdens] = useState<OrdemDespacho[]>([]);
  const [selecionada, setSelecionada] = useState<string | null>(null);
  const [sugestoes, setSugestoes] = useState<Sugestoes | null>(null);
  const [simulador, setSimulador] = useState<StatusSimulador | null>(null);
  const [desfecho, setDesfecho] = useState('');
  const [ocupado, setOcupado] = useState(false);
  const [ultimoEvento, setUltimoEvento] = useState<string>('');
  // comunicados operacionais (chegada ao local etc.) — ficam listados, não só no toast
  const [comunicados, setComunicados] = useState<{ id: string; em: string; texto: string }[]>([]);

  const carregar = useCallback(async () => {
    try {
      const [vs, os, ods, sim] = await Promise.all([
        viaturasService.listar(),
        ocorrenciasService.listar(['VALIDADA', 'EM_ATENDIMENTO'], 200),
        despachoService.listar(true),
        viaturasService.simulador().catch(() => null),
      ]);
      setViaturas(vs);
      setOcorrencias(os.itens);
      setOrdens(ods);
      setSimulador(sim);
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    }
  }, [avisar]);

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
    setUltimoEvento(`${e.tipo} ${new Date(e.ocorrido_em).toLocaleTimeString()}`);
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
        ocorrenciasService.listar(['VALIDADA', 'EM_ATENDIMENTO'], 200).then((p) => setOcorrencias(p.itens)).catch(() => undefined);
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

  const ocorrenciaSel = useMemo(() => ocorrencias.find((o) => o.ocorrencia_id === selecionada) ?? null, [ocorrencias, selecionada]);
  const semSinal = viaturas.filter((v) => v.sinal !== 'OK');

  const selecionar = async (id: string) => {
    setSelecionada(id);
    setSugestoes(null);
    const o = ocorrencias.find((x) => x.ocorrencia_id === id);
    if (o?.status === 'VALIDADA' && podeDespachar) {
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
        <button className="btn btn-ghost" onClick={carregar}>{t('common:actions.atualizar')}</button>
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
          <MapaTatico viaturas={viaturas} ocorrencias={ocorrencias} ordens={ordens} selecionada={selecionada} onSelecionarOcorrencia={selecionar} />
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
                      <td>{v.latitude !== null ? `${v.latitude.toFixed(4)}, ${v.longitude?.toFixed(4)} · ${new Date(v.posicao_registrada_em!).toLocaleTimeString()}` : t('painel:sem_sinal.nunca')}</td>
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
                  <li key={c.id}><span>🚓 {c.texto}<br /><small className="muted">{new Date(c.em).toLocaleTimeString()}</small></span></li>
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
                  <StatusBadge status={o.status} />
                </li>
              ))}
            </ul>
          </section>

          {ocorrenciaSel && podeDespachar && ocorrenciaSel.status === 'VALIDADA' && (
            <section className="card">
              <h3>{t('painel:despacho.titulo', { protocolo: ocorrenciaSel.numero_protocolo })}</h3>
              {!sugestoes && <p className="muted">{t('common:actions.loading')}</p>}
              {sugestoes && sugestoes.sugestoes.length > 0 && (
                <ul className="lista">
                  {sugestoes.sugestoes.map((s, i) => (
                    <li key={s.viatura.id}>
                      <span>#{i + 1} <strong>{s.viatura.prefixo}</strong> · {s.distancia_km.toFixed(2)} km</span>
                      <button className="btn btn-primary btn-sm" disabled={ocupado} onClick={() => despachar(s.viatura.id)}>{t('painel:despacho.despachar')}</button>
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
                  <li key={o.id}><span><strong>{o.numero}</strong> · {viaturas.find((v) => v.id === o.viatura_id)?.prefixo} · {new Date(o.criada_em).toLocaleTimeString()}</span></li>
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
    </div>
  );
};
