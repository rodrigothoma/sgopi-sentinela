import React, { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { OcorrenciaDetalheView } from '../components/ocorrencias/OcorrenciaDetalhe';
import { StatusBadge } from '../components/StatusBadge';
import { formatarNatureza } from '../utils/formatarNatureza';
import { useToast } from '../hooks/useToast';
import { mensagemDeErro } from '../services/api';
import { ocorrenciasService } from '../services/ocorrenciasService';
import type { OcorrenciaDetalhe, OcorrenciaResumo, StatusOcorrencia } from '../types/api';

const FILTROS: StatusOcorrencia[][] = [['AGUARDANDO_REVISAO'], ['EM_CORRECAO'], ['VALIDADA', 'EM_ATENDIMENTO'], ['REJEITADA', 'ENCERRADA']];

/** Delegado: fila de triagem (mais antiga primeiro) e decisões validar/devolver/rejeitar (RF04*, RF13). */
export const FilaDelegadoPage: React.FC = () => {
  const { t } = useTranslation(['ocorrencias', 'common']);
  const { avisar } = useToast();
  const [filtro, setFiltro] = useState(0);
  const [pagina, setPagina] = useState<{ itens: OcorrenciaResumo[]; total: number }>({ itens: [], total: 0 });
  const [detalhe, setDetalhe] = useState<OcorrenciaDetalhe | null>(null);
  const [justificativa, setJustificativa] = useState('');
  const [ocupado, setOcupado] = useState(false);

  const carregar = useCallback(async () => {
    try {
      const p = await ocorrenciasService.listar(FILTROS[filtro], 100);
      setPagina({ itens: p.itens, total: p.total });
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    }
  }, [filtro, avisar]);

  useEffect(() => {
    carregar();
  }, [carregar]);

  const decidir = async (acao: 'validar' | 'devolver' | 'rejeitar') => {
    if (!detalhe) return;
    if (acao !== 'validar' && justificativa.trim().length < 10) {
      avisar(t('ocorrencias:revisao.justificativa_curta'), 'erro');
      return;
    }
    if (acao === 'rejeitar' && !window.confirm(t('ocorrencias:revisao.confirmar_rejeicao'))) return;
    setOcupado(true);
    try {
      const id = detalhe.ocorrencia_id;
      const r = acao === 'validar' ? await ocorrenciasService.validar(id)
        : acao === 'devolver' ? await ocorrenciasService.devolver(id, justificativa)
        : await ocorrenciasService.rejeitar(id, justificativa);
      setDetalhe(r);
      setJustificativa('');
      avisar(t(`ocorrencias:revisao.ok_${acao}`), 'sucesso');
      carregar();
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    } finally {
      setOcupado(false);
    }
  };

  return (
    <div className="pagina duas-colunas">
      <section className="card">
        <h2>{t('ocorrencias:fila.titulo')} <span className="muted">({pagina.total})</span></h2>
        <div className="tabs">
          {FILTROS.map((_, i) => (
            <button key={i} className={`tab ${i === filtro ? 'ativo' : ''}`} onClick={() => setFiltro(i)}>{t(`ocorrencias:fila.filtro_${i}`)}</button>
          ))}
        </div>
        {pagina.itens.length === 0 && <p className="muted">{t('ocorrencias:fila.vazia')}</p>}
        <ul className="lista clicavel">
          {pagina.itens.map((o) => (
            <li key={o.ocorrencia_id} className={detalhe?.ocorrencia_id === o.ocorrencia_id ? 'ativo' : ''} onClick={async () => setDetalhe(await ocorrenciasService.buscarPorId(o.ocorrencia_id))}>
              <span><strong>{o.numero_protocolo}</strong> · {formatarNatureza(o.natureza, t)}<br /><small className="muted">{new Date(o.criada_em).toLocaleString()}</small></span>
              <StatusBadge status={o.status} />
            </li>
          ))}
        </ul>
      </section>
      <section className="card">
        {!detalhe && <p className="muted">{t('ocorrencias:fila.selecione')}</p>}
        {detalhe && (
          <>
            <OcorrenciaDetalheView o={detalhe} />
            {detalhe.status === 'AGUARDANDO_REVISAO' && (
              <div className="painel-decisao">
                <label>
                  {t('ocorrencias:revisao.justificativa_label')}
                  <textarea rows={3} value={justificativa} onChange={(e) => setJustificativa(e.target.value)} placeholder={t('ocorrencias:revisao.justificativa_placeholder')} />
                </label>
                <div className="acoes">
                  <button className="btn btn-primary" disabled={ocupado} onClick={() => decidir('validar')}>{t('ocorrencias:revisao.validar')}</button>
                  <button className="btn btn-warn" disabled={ocupado} onClick={() => decidir('devolver')}>{t('ocorrencias:revisao.devolver')}</button>
                  <button className="btn btn-danger" disabled={ocupado} onClick={() => decidir('rejeitar')}>{t('ocorrencias:revisao.rejeitar')}</button>
                </div>
              </div>
            )}
          </>
        )}
      </section>
    </div>
  );
};
