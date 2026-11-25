import React, { useCallback, useEffect, useState } from 'react';
import { Link, Navigate, useParams, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { OcorrenciaDetalheView } from '../components/ocorrencias/OcorrenciaDetalhe';
import { PainelPrioridade } from '../components/ocorrencias/PainelPrioridade';
import { useConfirmacao } from '../components/common/ConfirmDialog';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../hooks/useToast';
import { mensagemDeErro } from '../services/api';
import { ocorrenciasService } from '../services/ocorrenciasService';
import {
  STATUS_ARQUIVAVEIS, STATUS_EXCLUIVEIS, STATUS_PRIORIZAVEIS,
  type OcorrenciaDetalhe,
} from '../types/api';
import {
  abaDoStatus, GRUPOS_FILA_DELEGADO, lerAba, urlDaLista,
} from '../utils/ocorrenciaDeepLink';

const MINIMO_MOTIVO = 10;

export const FilaDelegadoDetalhePage: React.FC = () => {
  const { t } = useTranslation(['ocorrencias', 'common']);
  const { avisar } = useToast();
  const { tem } = useAuth();
  const { ocorrenciaId = '' } = useParams();
  const [searchParams] = useSearchParams();
  const [detalhe, setDetalhe] = useState<OcorrenciaDetalhe | null>(null);
  const [justificativa, setJustificativa] = useState('');
  const [motivo, setMotivo] = useState('');
  const [ocupado, setOcupado] = useState(false);
  const [confirmar, dialogoConfirmacao] = useConfirmacao();

  const carregar = useCallback(async () => {
    if (!ocorrenciaId) return;
    try {
      setDetalhe(await ocorrenciasService.buscarPorId(ocorrenciaId));
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    }
  }, [ocorrenciaId, avisar]);

  useEffect(() => {
    void carregar();
  }, [carregar]);

  const decidir = async (acao: 'validar' | 'devolver' | 'rejeitar') => {
    if (!detalhe) return;
    if (acao !== 'validar' && justificativa.trim().length < MINIMO_MOTIVO) {
      avisar(t('ocorrencias:revisao.justificativa_curta'), 'erro');
      return;
    }
    if (acao === 'rejeitar' && !(await confirmar(t('ocorrencias:revisao.confirmar_rejeicao')))) return;
    setOcupado(true);
    try {
      const r = acao === 'validar' ? await ocorrenciasService.validar(detalhe.ocorrencia_id, justificativa.trim())
        : acao === 'devolver' ? await ocorrenciasService.devolver(detalhe.ocorrencia_id, justificativa)
          : await ocorrenciasService.rejeitar(detalhe.ocorrencia_id, justificativa);
      setDetalhe(r);
      setJustificativa('');
      avisar(t(`ocorrencias:revisao.ok_${acao}`), 'sucesso');
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    } finally {
      setOcupado(false);
    }
  };

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
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    } finally {
      setOcupado(false);
    }
  };

  if (!ocorrenciaId) return <Navigate to="/fila" replace />;

  const aba = detalhe
    ? abaDoStatus(detalhe.status)
    : lerAba(searchParams, GRUPOS_FILA_DELEGADO.length);
  const voltar = urlDaLista('/fila', searchParams, aba);
  const podeArquivar = !!detalhe && STATUS_ARQUIVAVEIS.includes(detalhe.status);
  const podeExcluir = !!detalhe && STATUS_EXCLUIVEIS.includes(detalhe.status);

  return (
    <div className="pagina detalhe-pagina">
      {dialogoConfirmacao}
      <Link className="btn btn-ghost btn-sm voltar" to={voltar}>
        ← {t('ocorrencias:fila.voltar')}
      </Link>
      <section className="card">
        {!detalhe && <p className="muted">{t('ocorrencias:fila.selecione')}</p>}
        {detalhe && (
          <>
            <OcorrenciaDetalheView o={detalhe} onAlterada={() => void carregar()} />
            {tem('DELEGADO') && STATUS_PRIORIZAVEIS.includes(detalhe.status) && (
              <PainelPrioridade detalhe={detalhe} onAlterada={setDetalhe} />
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
                  <button className="btn btn-primary" disabled={ocupado} onClick={() => void decidir('validar')}>{t('ocorrencias:revisao.validar')}</button>
                  {detalhe.origem !== 'PUBLICA' && (
                    <button className="btn btn-warn" disabled={ocupado} onClick={() => void decidir('devolver')}>{t('ocorrencias:revisao.devolver')}</button>
                  )}
                  <button className="btn btn-danger" disabled={ocupado} onClick={() => void decidir('rejeitar')}>{t('ocorrencias:revisao.rejeitar')}</button>
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
                    <button className="btn btn-warn" disabled={ocupado} onClick={() => void administrar('arquivar')}>{t('ocorrencias:admin.arquivar')}</button>
                  )}
                  {podeExcluir && (
                    <button className="btn btn-danger" disabled={ocupado} onClick={() => void administrar('excluir')}>{t('ocorrencias:admin.excluir')}</button>
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
