import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Navigate, useNavigate, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { FiltrosOcorrenciasBar } from '../components/ocorrencias/FiltrosOcorrencias';
import { PrioridadeBadge } from '../components/PrioridadeBadge';
import { StatusBadge } from '../components/StatusBadge';
import { useFiltrosOcorrenciasUrl } from '../hooks/useFiltrosOcorrenciasUrl';
import { useTempoRealListener } from '../hooks/useTempoReal';
import { useToast } from '../hooks/useToast';
import { EsperaBadge } from '../components/ocorrencias/EsperaBadge';
import { mensagemDeErro } from '../services/api';
import { ocorrenciasService } from '../services/ocorrenciasService';
import { formatarNatureza } from '../utils/formatarNatureza';
import { inserirOrdenado, resumoDaNotificacao } from '../utils/filaDelegado';
import { GRUPOS_FILA_DELEGADO, idOcorrenciaLegada, lerAba, urlDoDetalhe } from '../utils/ocorrenciaDeepLink';
import { formatarDataHora } from '../utils/datas';
import type { EventoTempoReal, OcorrenciaResumo } from '../types/api';

export const FilaDelegadoPage: React.FC = () => {
  const { t } = useTranslation(['ocorrencias', 'common']);
  const { avisar } = useToast();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const legado = idOcorrenciaLegada(searchParams);
  const [filtro, setFiltro] = useState(() => lerAba(searchParams, GRUPOS_FILA_DELEGADO.length));
  const [pagina, setPagina] = useState<{ itens: OcorrenciaResumo[]; total: number }>({ itens: [], total: 0 });
  const [exportando, setExportando] = useState(false);
  const [filtros, aplicarFiltros] = useFiltrosOcorrenciasUrl();
  const [novas, setNovas] = useState<Set<string>>(new Set());
  const ultimaRequisicao = useRef(0);

  const carregar = useCallback(async () => {
    if (legado) return;
    const requisicao = ++ultimaRequisicao.current;
    try {
      const p = await ocorrenciasService.listar([...GRUPOS_FILA_DELEGADO[filtro]], 100, 0, false, filtros, true);
      if (requisicao !== ultimaRequisicao.current) return;
      setPagina({ itens: p.itens, total: p.total });
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    }
  }, [filtro, filtros, avisar, legado]);

  const exportar = async () => {
    setExportando(true);
    try {
      await ocorrenciasService.exportarCsv([...GRUPOS_FILA_DELEGADO[filtro]], filtros);
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    } finally {
      setExportando(false);
    }
  };

  useEffect(() => {
    void carregar();
  }, [carregar]);

  useTempoRealListener({
    onEvento: (e: EventoTempoReal) => {
      if (e.tipo !== 'OcorrenciaCriada' || !GRUPOS_FILA_DELEGADO[filtro].includes('AGUARDANDO_REVISAO')) return;
      const d = e.dados as Record<string, unknown>;
      if (Object.values(filtros).some(Boolean)) {
        void carregar();
        return;
      }
      const id = String(d.ocorrencia_id ?? '');
      if (!id || pagina.itens.some((o) => o.ocorrencia_id === id)) return;
      setPagina((p) => ({ itens: inserirOrdenado(p.itens, resumoDaNotificacao(d)), total: p.total + 1 }));
      setNovas((s) => new Set(s).add(id));
    },
    onReconectar: carregar,
  });

  const trocarAba = useCallback((indice: number) => {
    setFiltro(indice);
    setSearchParams((atual) => {
      const proxima = new URLSearchParams(atual);
      proxima.delete('ocorrencia');
      proxima.set('aba', String(indice));
      return proxima;
    }, { replace: true });
  }, [setSearchParams]);

  const abrir = useCallback((id: string) => {
    setNovas((s) => {
      if (!s.has(id)) return s;
      const copia = new Set(s);
      copia.delete(id);
      return copia;
    });
    navigate(urlDoDetalhe('/fila', id, searchParams));
  }, [navigate, searchParams]);

  if (legado) return <Navigate to={urlDoDetalhe('/fila', legado, searchParams)} replace />;

  return (
    <div className="pagina">
      <section className="card">
        <div className="cabecalho-lista">
          <h2>{t('ocorrencias:fila.titulo')} <span className="muted">({pagina.total})</span></h2>
          <button className="btn btn-ghost btn-sm" disabled={exportando || pagina.total === 0} onClick={() => void exportar()} title={t('ocorrencias:filtros.exportar_dica')}>
            {t('ocorrencias:filtros.exportar_csv')}
          </button>
        </div>
        <FiltrosOcorrenciasBar valor={filtros} onAplicar={aplicarFiltros} mostrarOrigem />
        <div className="tabs">
          {GRUPOS_FILA_DELEGADO.map((_, i) => (
            <button key={i} className={`tab ${i === filtro ? 'ativo' : ''}`} onClick={() => trocarAba(i)}>
              {t(`ocorrencias:fila.filtro_${i}`)}
            </button>
          ))}
        </div>
        {pagina.itens.length === 0 && <p className="muted">{t('ocorrencias:fila.vazia')}</p>}
        <ul className="lista clicavel">
          {pagina.itens.map((o) => (
            <li key={o.ocorrencia_id} onClick={() => abrir(o.ocorrencia_id)}>
              <span><strong>{o.numero_protocolo}</strong> · {formatarNatureza(o.natureza, t)}<br /><small className="muted">{formatarDataHora(o.criada_em)}</small></span>
              <span className="lista-badges">
                {novas.has(o.ocorrencia_id) && <span className="badge-nova">{t('ocorrencias:fila.nova')}</span>}
                <EsperaBadge desde={o.criada_em} status={o.status} /><StatusBadge status={o.status} /><PrioridadeBadge prioridade={o.prioridade} />
              </span>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
};
