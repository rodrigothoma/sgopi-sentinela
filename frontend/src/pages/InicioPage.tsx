import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { StatusBadge } from '../components/StatusBadge';
import { useAuth } from '../hooks/useAuth';
import { useTempoReal } from '../hooks/useTempoReal';
import { useToast } from '../hooks/useToast';
import { mensagemDeErro } from '../services/api';
import { despachoService } from '../services/despachoService';
import { ocorrenciasService } from '../services/ocorrenciasService';
import { sessao } from '../services/sessao';
import { usuariosService } from '../services/usuariosService';
import { viaturasService } from '../services/viaturasService';
import type { EventoTempoReal, OcorrenciaResumo, OrdemDespacho, Papel, SituacaoViatura, StatusOcorrencia, Usuario, Viatura } from '../types/api';

/** Ocorrências que ainda exigem trabalho de alguém — o que a tela chama de "investigações em andamento". */
const STATUS_EM_ANDAMENTO: readonly StatusOcorrencia[] = ['EM_ATENDIMENTO', 'VALIDADA', 'AGUARDANDO_REVISAO', 'EM_CORRECAO'];
const SITUACOES_ATIVAS: readonly SituacaoViatura[] = ['DISPONIVEL', 'EM_DESLOCAMENTO', 'OPERANDO'];
const PAPEIS_ESCALA: readonly Papel[] = ['DELEGADO', 'SUPERVISOR', 'OPERADOR_CENTRAL', 'AGENTE', 'ESCRIVAO', 'PERITO'];
/** Turnos de 8 h (alinhados ao JWT de turno). */
const TURNOS = [
  { id: 'MANHA', inicio: 6, fim: 14 },
  { id: 'TARDE', inicio: 14, fim: 22 },
  { id: 'NOITE', inicio: 22, fim: 6 },
] as const;

const turnoDe = (hora: number) => TURNOS.find((t) => (t.inicio < t.fim ? hora >= t.inicio && hora < t.fim : hora >= t.inicio || hora < t.fim)) ?? TURNOS[0];
const saudacaoDe = (hora: number) => (hora < 12 ? 'manha' : hora < 18 ? 'tarde' : 'noite');
const mesmoDia = (iso: string, ref: Date) => new Date(iso).toDateString() === ref.toDateString();
const hh = (h: number) => `${String(h).padStart(2, '0')}:00`;

function rotaListagem(papel: Papel): string {
  if (papel === 'AGENTE') return '/minhas';
  if (papel === 'DELEGADO') return '/fila';
  return '/painel';
}

/**
 * Tela inicial pós-login (delegado/agente/operador): frota em atividade, efetivo em campo,
 * últimas ocorrências, investigações em andamento e escala do turno. Carga por REST e
 * atualização por WebSocket; agente enxerga só as próprias ocorrências (regra do backend).
 */
export const InicioPage: React.FC = () => {
  const { t, i18n } = useTranslation(['inicio', 'common']);
  const { usuario, tem } = useAuth();
  const { avisar } = useToast();
  const veOrdens = tem('OPERADOR_CENTRAL', 'SUPERVISOR', 'DELEGADO');
  const [viaturas, setViaturas] = useState<Viatura[]>([]);
  const [ocorrencias, setOcorrencias] = useState<OcorrenciaResumo[]>([]);
  const [ordens, setOrdens] = useState<OrdemDespacho[]>([]);
  const [usuarios, setUsuarios] = useState<Usuario[]>([]);
  const [agora, setAgora] = useState(() => new Date());

  const carregar = useCallback(async () => {
    try {
      const [vs, os, ods, us] = await Promise.all([
        viaturasService.listar(),
        ocorrenciasService.listar([], 200),
        veOrdens ? despachoService.listar(true) : Promise.resolve([] as OrdemDespacho[]),
        usuariosService.listar(),
      ]);
      setViaturas(vs);
      setOcorrencias(os.itens);
      setOrdens(ods);
      setUsuarios(us);
      setAgora(new Date());
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    }
  }, [avisar, veOrdens]);

  useEffect(() => {
    carregar();
  }, [carregar]);

  // relógio da tela + "sinal" recalculado no cliente para viaturas que pararam de emitir (RNF04*)
  useEffect(() => {
    const id = window.setInterval(() => {
      setAgora(new Date());
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
    const d = e.dados as Record<string, string | number | null>;
    switch (e.tipo) {
      case 'PosicaoAtualizada':
      case 'ViaturaSituacaoAlterada':
      case 'ViaturaChegouAoLocal':
        setViaturas((vs) => vs.map((v) => v.id === d.viatura_id
          ? { ...v, situacao: (d.situacao as SituacaoViatura) ?? v.situacao, latitude: (d.latitude as number) ?? v.latitude, longitude: (d.longitude as number) ?? v.longitude, posicao_registrada_em: (d.registrada_em as string) ?? v.posicao_registrada_em, sinal: d.latitude != null ? 'OK' : v.sinal }
          : v));
        break;
      default:
        // demais eventos mudam ocorrências/ordens — recarga simples é suficiente para uma tela-resumo
        carregar();
        break;
    }
  }, [carregar]);

  useTempoReal(onEvento, carregar);

  const hora = agora.getHours();
  const turno = turnoDe(hora);
  const expiraEm = sessao.ler()?.expira_em;

  const viaturasAtivas = useMemo(() => viaturas.filter((v) => SITUACOES_ATIVAS.includes(v.situacao)), [viaturas]);
  const emAndamento = useMemo(
    () => ocorrencias
      .filter((o) => STATUS_EM_ANDAMENTO.includes(o.status))
      .sort((a, b) => STATUS_EM_ANDAMENTO.indexOf(a.status) - STATUS_EM_ANDAMENTO.indexOf(b.status) || b.atualizada_em.localeCompare(a.atualizada_em)),
    [ocorrencias],
  );
  const ultimas = useMemo(() => [...ocorrencias].sort((a, b) => b.criada_em.localeCompare(a.criada_em)).slice(0, 8), [ocorrencias]);
  const hoje = useMemo(() => ocorrencias.filter((o) => mesmoDia(o.criada_em, agora)), [ocorrencias, agora]);
  const agentes = useMemo(() => usuarios.filter((u) => u.papel === 'AGENTE'), [usuarios]);
  const ocorrenciasPorAgente = useMemo(() => {
    const m = new Map<string, number>();
    emAndamento.forEach((o) => m.set(o.agente_policial_id, (m.get(o.agente_policial_id) ?? 0) + 1));
    return m;
  }, [emAndamento]);
  const emCampo = agentes.filter((a) => (ocorrenciasPorAgente.get(a.id) ?? 0) > 0);
  const protocoloDaViatura = (viaturaId: string) => {
    const ordem = ordens.find((o) => o.viatura_id === viaturaId && o.ativa);
    return ordem ? ocorrencias.find((o) => o.ocorrencia_id === ordem.ocorrencia_id)?.numero_protocolo ?? null : null;
  };
  const prefixoDaOcorrencia = (ocorrenciaId: string) => {
    const ordem = ordens.find((o) => o.ocorrencia_id === ocorrenciaId && o.ativa);
    return ordem ? viaturas.find((v) => v.id === ordem.viatura_id)?.prefixo ?? null : null;
  };
  const efetivo = PAPEIS_ESCALA.map((papel) => ({ papel, pessoas: usuarios.filter((u) => u.papel === papel) })).filter((g) => g.pessoas.length > 0);

  if (!usuario) return null;

  return (
    <div className="pagina inicio">
      <header className="inicio-cabecalho">
        <div>
          <h1>{t(`inicio:saudacao.${saudacaoDe(hora)}`, { nome: usuario.nome })}</h1>
          <p className="muted">
            {t('inicio:subtitulo', { data: agora.toLocaleDateString(i18n.language, { weekday: 'long', day: 'numeric', month: 'long' }) })} · <span className="pill">{t(`common:papel.${usuario.papel}`)}</span>
          </p>
        </div>
        <div className="inicio-turno">
          <span className="kpi-label">{t('inicio:turno_atual')}</span>
          <strong>{t(`inicio:turnos.${turno.id}`)} · {t('inicio:escala.horario', { inicio: hh(turno.inicio), fim: hh(turno.fim) })}</strong>
          {expiraEm && <small className="muted">{t('inicio:sessao_encerra', { hora: new Date(expiraEm).toLocaleTimeString(i18n.language, { hour: '2-digit', minute: '2-digit' }) })}</small>}
        </div>
      </header>

      <div className="kpi-grid">
        <div className="kpi-card">
          <span className="kpi-label">{t('inicio:kpi.viaturas_ativas')}</span>
          <span className="kpi-val" style={{ color: 'var(--ok)' }}>{viaturasAtivas.length}</span>
          <span className="kpi-sub">{t('inicio:kpi.de_total', { total: viaturas.length })}</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-label">{t('inicio:kpi.funcionarios_campo')}</span>
          <span className="kpi-val" style={{ color: 'var(--primary)' }}>{emCampo.length}</span>
          <span className="kpi-sub">{t('inicio:kpi.de_agentes', { total: agentes.length })}</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-label">{t('inicio:kpi.investigacoes')}</span>
          <span className="kpi-val">{emAndamento.length}</span>
          <span className="kpi-sub">{t('inicio:kpi.em_atendimento', { n: emAndamento.filter((o) => o.status === 'EM_ATENDIMENTO').length })}</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-label">{t('inicio:kpi.ocorrencias_hoje')}</span>
          <span className="kpi-val">{hoje.length}</span>
          <span className="kpi-sub" style={{ color: hoje.some((o) => o.status === 'AGUARDANDO_REVISAO') ? 'var(--warn)' : undefined }}>
            {t('inicio:kpi.aguardando_revisao', { n: hoje.filter((o) => o.status === 'AGUARDANDO_REVISAO').length })}
          </span>
        </div>
      </div>

      <div className="inicio-grid">
        <section className="card">
          <h3>🚓 {t('inicio:viaturas.titulo')} <span className="muted">({viaturasAtivas.length})</span></h3>
          {viaturasAtivas.length === 0 && <p className="muted">{t('inicio:viaturas.vazio')}</p>}
          {viaturasAtivas.length > 0 && (
            <table className="tabela compacta">
              <thead>
                <tr>
                  <th>{t('inicio:viaturas.viatura')}</th>
                  <th>{t('inicio:viaturas.situacao')}</th>
                  <th>{t('inicio:viaturas.sinal')}</th>
                  {veOrdens && <th>{t('inicio:viaturas.atendendo')}</th>}
                </tr>
              </thead>
              <tbody>
                {viaturasAtivas.map((v) => (
                  <tr key={v.id}>
                    <td><strong>{v.prefixo}</strong> <small className="muted">{v.placa}</small></td>
                    <td><StatusBadge status={v.situacao} grupo="situacao" /></td>
                    <td><StatusBadge status={v.sinal} grupo="sinal" /></td>
                    {veOrdens && <td>{protocoloDaViatura(v.id) ?? <span className="muted">{t('inicio:viaturas.livre')}</span>}</td>}
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>

        <section className="card">
          <h3>👮 {t('inicio:funcionarios.titulo')} <span className="muted">({emCampo.length}/{agentes.length})</span></h3>
          {tem('AGENTE') && <p className="muted small">{t('inicio:funcionarios.somente_proprias')}</p>}
          {agentes.length === 0 && <p className="muted">{t('inicio:funcionarios.vazio')}</p>}
          <ul className="lista">
            {agentes.map((a) => {
              const n = ocorrenciasPorAgente.get(a.id) ?? 0;
              return (
                <li key={a.id}>
                  <span>
                    <strong>{a.nome}</strong>{a.id === usuario.id && <span className="muted"> ({t('inicio:escala.voce')})</span>}
                    <br /><small className="muted">{t('inicio:funcionarios.ocorrencias', { n })}</small>
                  </span>
                  <span className={`badge ${n > 0 ? 'badge-EM_ATENDIMENTO' : 'badge-DISPONIVEL'}`}>{n > 0 ? t('inicio:funcionarios.em_campo') : t('inicio:funcionarios.prontidao')}</span>
                </li>
              );
            })}
          </ul>
        </section>

        <section className="card">
          <h3>
            📋 {t('inicio:ultimas.titulo')}
            <Link className="btn btn-link btn-sm inicio-ver-todas" to={rotaListagem(usuario.papel)}>{t('inicio:ultimas.ver_todas')} →</Link>
          </h3>
          {ultimas.length === 0 && <p className="muted">{t('inicio:ultimas.vazio')}</p>}
          <ul className="lista">
            {ultimas.map((o) => (
              <li key={o.ocorrencia_id}>
                <span>
                  <strong>{o.numero_protocolo}</strong> · {o.natureza}
                  <br /><small className="muted">{o.localizacao} · {new Date(o.criada_em).toLocaleString(i18n.language, { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}</small>
                </span>
                <StatusBadge status={o.status} />
              </li>
            ))}
          </ul>
        </section>

        <section className="card">
          <h3>🔎 {t('inicio:investigacoes.titulo')} <span className="muted">({emAndamento.length})</span></h3>
          {emAndamento.length === 0 && <p className="muted">{t('inicio:investigacoes.vazio')}</p>}
          <ul className="lista">
            {emAndamento.slice(0, 8).map((o) => {
              const prefixo = prefixoDaOcorrencia(o.ocorrencia_id);
              return (
                <li key={o.ocorrencia_id}>
                  <span>
                    <strong>{o.numero_protocolo}</strong> · {o.natureza}
                    <br />
                    <small className="muted">
                      {t('inicio:investigacoes.fato_em', { quando: new Date(o.data_hora_fato).toLocaleString(i18n.language, { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }) })}
                      {prefixo && <> · 🚓 {t('inicio:investigacoes.viatura', { prefixo })}</>}
                    </small>
                  </span>
                  <StatusBadge status={o.status} />
                </li>
              );
            })}
          </ul>
        </section>

        <section className="card inicio-escala">
          <h3>🗓️ {t('inicio:escala.titulo')}</h3>
          <div className="escala-turnos">
            {TURNOS.map((tr) => (
              <div key={tr.id} className={`escala-turno ${tr.id === turno.id ? 'atual' : ''}`}>
                <strong>{t(`inicio:turnos.${tr.id}`)}</strong>
                <small className="muted">{t('inicio:escala.horario', { inicio: hh(tr.inicio), fim: hh(tr.fim) })}</small>
                {tr.id === turno.id && <span className="badge badge-OK">{t('inicio:escala.atual')}</span>}
              </div>
            ))}
          </div>
          <h4>{t('inicio:escala.efetivo')} <span className="muted">({usuarios.length})</span></h4>
          {efetivo.map((g) => (
            <div key={g.papel} className="efetivo-grupo">
              <span className="kpi-label">{t(`common:papel.${g.papel}`)}</span>
              <div className="chips">
                {g.pessoas.map((p) => (
                  <span key={p.id} className={`chip ${p.id === usuario.id ? 'voce' : ''}`}>{p.nome}{p.id === usuario.id && ` · ${t('inicio:escala.voce')}`}</span>
                ))}
              </div>
            </div>
          ))}
        </section>
      </div>
    </div>
  );
};
