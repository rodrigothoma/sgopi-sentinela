import React, { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { OcorrenciaDetalheView } from '../components/ocorrencias/OcorrenciaDetalhe';
import { StatusBadge } from '../components/StatusBadge';
import { useToast } from '../hooks/useToast';
import { mensagemDeErro } from '../services/api';
import { ocorrenciasService } from '../services/ocorrenciasService';
import { STATUS_ARQUIVAVEIS, STATUS_EXCLUIVEIS, type OcorrenciaDetalhe, type OcorrenciaResumo, type StatusOcorrencia } from '../types/api';

const FILTROS: StatusOcorrencia[][] = [
  ['AGUARDANDO_REVISAO'], ['EM_CORRECAO'], ['VALIDADA', 'EM_ATENDIMENTO'], ['REJEITADA', 'ENCERRADA'], ['ARQUIVADA', 'EXCLUIDA'],
];
const MINIMO_MOTIVO = 10;

/**
 * Delegado: fila de triagem (mais antiga primeiro), decisões validar/devolver/rejeitar (RF04*, RF13)
 * e atos administrativos arquivar/excluir com motivo obrigatório (RF20).
 */
export const FilaDelegadoPage: React.FC = () => {
  const { t } = useTranslation(['ocorrencias', 'common']);
  const { avisar } = useToast();
  const [filtro, setFiltro] = useState(0);
  const [pagina, setPagina] = useState<{ itens: OcorrenciaResumo[]; total: number }>({ itens: [], total: 0 });
  const [detalhe, setDetalhe] = useState<OcorrenciaDetalhe | null>(null);
  const [justificativa, setJustificativa] = useState('');
  const [motivo, setMotivo] = useState('');
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

  const abrir = async (id: string) => {
    setMotivo('');
    setJustificativa('');
    setDetalhe(await ocorrenciasService.buscarPorId(id));
  };

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

  /** Arquivar/excluir: autorização do Delegado (papel já garantido pela rota) + motivo obrigatório. */
  const administrar = async (acao: 'arquivar' | 'excluir') => {
    if (!detalhe) return;
    if (motivo.trim().length < MINIMO_MOTIVO) {
      avisar(t('ocorrencias:admin.motivo_curto'), 'erro');
      return;
    }
    if (!window.confirm(t(`ocorrencias:admin.confirmar_${acao}`, { protocolo: detalhe.numero_protocolo }))) return;
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
            <li key={o.ocorrencia_id} className={detalhe?.ocorrencia_id === o.ocorrencia_id ? 'ativo' : ''} onClick={() => abrir(o.ocorrencia_id)}>
              <span><strong>{o.numero_protocolo}</strong> · {o.natureza}<br /><small className="muted">{new Date(o.criada_em).toLocaleString()}</small></span>
              <StatusBadge status={o.status} />
            </li>
          ))}
        </ul>
      </section>
      <section className="card">
        {!detalhe && <p className="muted">{t('ocorrencias:fila.selecione')}</p>}
        {detalhe && (
          <>
            <OcorrenciaDetalheView o={detalhe} onAlterada={() => void recarregarDetalhe()} />
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
