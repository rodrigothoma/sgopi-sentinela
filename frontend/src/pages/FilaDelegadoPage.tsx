import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { FiltrosOcorrenciasBar } from '../components/ocorrencias/FiltrosOcorrencias';
import { OcorrenciaDetalheView } from '../components/ocorrencias/OcorrenciaDetalhe';
import { PainelPrioridade } from '../components/ocorrencias/PainelPrioridade';
import { PrioridadeBadge } from '../components/PrioridadeBadge';
import { useAuth } from '../hooks/useAuth';
import { StatusBadge } from '../components/StatusBadge';
import { useConfirmacao } from '../components/common/ConfirmDialog';
import { useFiltrosOcorrenciasUrl } from '../hooks/useFiltrosOcorrenciasUrl';
import { useToast } from '../hooks/useToast';
import { mensagemDeErro } from '../services/api';
import { ocorrenciasService } from '../services/ocorrenciasService';
import { formatarNatureza } from '../utils/formatarNatureza';
import { STATUS_ARQUIVAVEIS, STATUS_EXCLUIVEIS, STATUS_PRIORIZAVEIS, type OcorrenciaDetalhe, type OcorrenciaResumo, type StatusOcorrencia } from '../types/api';
import { formatarDataHora } from '../utils/datas';

const FILTROS: StatusOcorrencia[][] = [
  ['AGUARDANDO_REVISAO'], ['EM_CORRECAO'], ['VALIDADA', 'EM_ATENDIMENTO'], ['REJEITADA', 'ENCERRADA'], ['ARQUIVADA', 'EXCLUIDA'],
];
const MINIMO_MOTIVO = 10;

/** Delegado: fila de triagem (mais antiga primeiro) e decisões validar/devolver/rejeitar (RF04*, RF01). */
export const FilaDelegadoPage: React.FC = () => {
  const { t } = useTranslation(['ocorrencias', 'common']);
  const { avisar } = useToast();
  const { tem } = useAuth();
  const [filtro, setFiltro] = useState(0);
  const [pagina, setPagina] = useState<{ itens: OcorrenciaResumo[]; total: number }>({ itens: [], total: 0 });
  const [detalhe, setDetalhe] = useState<OcorrenciaDetalhe | null>(null);

  const [justificativa, setJustificativa] = useState('');
  const [motivo, setMotivo] = useState('');
  const [ocupado, setOcupado] = useState(false);
  const [exportando, setExportando] = useState(false);
  const [confirmar, dialogoConfirmacao] = useConfirmacao();
  const [filtros, aplicarFiltros] = useFiltrosOcorrenciasUrl();

  const [searchParams] = useSearchParams();
  const paramOcorrenciaId = searchParams.get('ocorrencia');

  // Só a resposta da requisição mais recente vale: trocar de aba rápido não deixa
  // uma resposta atrasada da aba anterior sobrescrever a lista.
  const ultimaRequisicao = useRef(0);

  const carregar = useCallback(async () => {
    const requisicao = ++ultimaRequisicao.current;
    try {
      // Mais graves primeiro; dentro da mesma gravidade, a mais antiga (sugestão #7)
      const p = await ocorrenciasService.listar(FILTROS[filtro], 100, 0, false, filtros, true);
      if (requisicao !== ultimaRequisicao.current) return;
      setPagina({ itens: p.itens, total: p.total });
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    }
  }, [filtro, filtros, avisar]);

  /** CSV da aba e da busca atuais (a exportação fica registrada na trilha de auditoria). */
  const exportar = async () => {
    setExportando(true);
    try {
      await ocorrenciasService.exportarCsv(FILTROS[filtro], filtros);
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    } finally {
      setExportando(false);
    }
  };

  useEffect(() => {
    carregar();
  }, [carregar]);

  const abrir = useCallback(async (id: string) => {
    setMotivo('');
    setJustificativa('');
    try {
      setDetalhe(await ocorrenciasService.buscarPorId(id));
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    }
  }, [avisar]);

  useEffect(() => {
    if (paramOcorrenciaId) {
      abrir(paramOcorrenciaId);
    }
  }, [paramOcorrenciaId, abrir]);

  const recarregarDetalhe = async () => {
    if (!detalhe) return;
    try {
      setDetalhe(await ocorrenciasService.buscarPorId(detalhe.ocorrencia_id));
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    }
  };

  const decidir = async (acao: 'validar' | 'devolver' | 'rejeitar') => {
    if (!detalhe) return;
    if (acao !== 'validar' && justificativa.trim().length < 10) {
      avisar(t('ocorrencias:revisao.justificativa_curta'), 'erro');
      return;
    }
    if (acao === 'rejeitar' && !(await confirmar(t('ocorrencias:revisao.confirmar_rejeicao')))) return;
    setOcupado(true);
    try {
      const id = detalhe.ocorrencia_id;
      const r = acao === 'validar' ? await ocorrenciasService.validar(id, justificativa.trim())
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

  /** Arquivar/excluir: autorização do Delegado (papel já garantido pela rota) + motivo obrigatório. */
  const administrar = async (acao: 'arquivar' | 'excluir') => {
    if (!detalhe) return;
    if (motivo.trim().length < MINIMO_MOTIVO) {
      avisar(t('ocorrencias:admin.motivo_curto'), 'erro');
      return;
    }
    if (!(await confirmar(t(`ocorrencias:admin.confirmar_${acao}`, { protocolo: detalhe.numero_protocolo })))) return;
    setOcupado(true);
    try {
      const r = acao === 'arquivar'
        ? await ocorrenciasService.arquivar(detalhe.ocorrencia_id, motivo.trim())
        : await ocorrenciasService.excluir(detalhe.ocorrencia_id, motivo.trim());
      setDetalhe(r);
      setMotivo('');
      avisar(t(`ocorrencias:admin.ok_${acao}`), 'sucesso');
      carregar();
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    } finally {
      setOcupado(false);
    }
  };

  const podeArquivar = !!detalhe && STATUS_ARQUIVAVEIS.includes(detalhe.status);
  const podeExcluir = !!detalhe && STATUS_EXCLUIVEIS.includes(detalhe.status);

  return (
    <div className="pagina duas-colunas">
      {dialogoConfirmacao}
      <section className="card">
        <div className="cabecalho-lista">
          <h2>{t('ocorrencias:fila.titulo')} <span className="muted">({pagina.total})</span></h2>
          <button className="btn btn-ghost btn-sm" disabled={exportando || pagina.total === 0} onClick={exportar} title={t('ocorrencias:filtros.exportar_dica')}>
            {t('ocorrencias:filtros.exportar_csv')}
          </button>
        </div>
        <FiltrosOcorrenciasBar valor={filtros} onAplicar={aplicarFiltros} mostrarOrigem />
        <div className="tabs">
          {FILTROS.map((_, i) => (
            <button key={i} className={`tab ${i === filtro ? 'ativo' : ''}`} onClick={() => setFiltro(i)}>{t(`ocorrencias:fila.filtro_${i}`)}</button>
          ))}
        </div>
        {pagina.itens.length === 0 && <p className="muted">{t('ocorrencias:fila.vazia')}</p>}
        <ul className="lista clicavel">
          {pagina.itens.map((o) => (
            <li key={o.ocorrencia_id} className={detalhe?.ocorrencia_id === o.ocorrencia_id ? 'ativo' : ''} onClick={() => abrir(o.ocorrencia_id)}>
              <span><strong>{o.numero_protocolo}</strong> · {formatarNatureza(o.natureza, t)}<br /><small className="muted">{formatarDataHora(o.criada_em)}</small></span>
              <span className="lista-badges"><StatusBadge status={o.status} /><PrioridadeBadge prioridade={o.prioridade} /></span>
            </li>
          ))}
        </ul>
      </section>
      <section className="card">
        {!detalhe && <p className="muted">{t('ocorrencias:fila.selecione')}</p>}
        {detalhe && (
          <>
            <OcorrenciaDetalheView o={detalhe} onAlterada={() => void recarregarDetalhe()} />
            {tem('DELEGADO') && STATUS_PRIORIZAVEIS.includes(detalhe.status) && (
              <PainelPrioridade detalhe={detalhe} onAlterada={(r) => { setDetalhe(r); carregar(); }} />
            )}
            {detalhe.status === 'AGUARDANDO_REVISAO' && (
              <div className="painel-decisao">
                <label>
                  <strong>{t('ocorrencias:revisao.despacho_label')}</strong>
                  <small className="muted"> · {t('ocorrencias:revisao.justificativa_label')}</small>
                  <textarea id="justificativa-revisao" rows={3} maxLength={2000} value={justificativa} onChange={(e) => setJustificativa(e.target.value)} placeholder={t('ocorrencias:revisao.justificativa_placeholder')} />
                </label>
                {detalhe.origem === 'PUBLICA' && <p className="muted">{t('ocorrencias:revisao.publica_sem_devolucao')}</p>}
                <div className="acoes">
                  <button className="btn btn-primary" disabled={ocupado} onClick={() => decidir('validar')}>{t('ocorrencias:revisao.validar')}</button>
                  {detalhe.origem !== 'PUBLICA' && (
                    <button className="btn btn-warn" disabled={ocupado} onClick={() => decidir('devolver')}>{t('ocorrencias:revisao.devolver')}</button>
                  )}
                  <button className="btn btn-danger" disabled={ocupado} onClick={() => decidir('rejeitar')}>{t('ocorrencias:revisao.rejeitar')}</button>
                </div>
              </div>
            )}
            {(podeArquivar || podeExcluir) && (
              <div className="painel-admin">
                <h4>{t('ocorrencias:admin.titulo')}</h4>
                <p className="aviso-autorizacao">{t('ocorrencias:admin.aviso')}</p>
                <label htmlFor="motivo-admin">
                  {t('ocorrencias:admin.motivo_label')} <span className="muted contador">({motivo.trim().length}/{MINIMO_MOTIVO}+)</span>
                </label>
                <textarea id="motivo-admin" rows={3} maxLength={2000} value={motivo} onChange={(e) => setMotivo(e.target.value)} placeholder={t('ocorrencias:admin.motivo_placeholder')} />
                <div className="acoes">
                  {podeArquivar && (
                    <button className="btn btn-warn" disabled={ocupado} onClick={() => administrar('arquivar')}>{t('ocorrencias:admin.arquivar')}</button>
                  )}
                  {podeExcluir && (
                    <button className="btn btn-danger" disabled={ocupado} onClick={() => administrar('excluir')}>{t('ocorrencias:admin.excluir')}</button>
                  )}
                </div>
              </div>
            )}
            {detalhe.status === 'EM_ATENDIMENTO' && <p className="muted small">{t('ocorrencias:admin.bloqueado_atendimento')}</p>}
          </>
        )}
      </section>
    </div>
  );
};
