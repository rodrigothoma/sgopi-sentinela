import React, { useCallback, useEffect, useState } from 'react';
import { Link, Navigate, useParams, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { OcorrenciaDetalheView } from '../components/ocorrencias/OcorrenciaDetalhe';
import { OcorrenciaForm, paraInputLocal, paraRequest, type ValoresOcorrencia } from '../components/ocorrencias/OcorrenciaForm';
import { useToast } from '../hooks/useToast';
import { mensagemDeErro } from '../services/api';
import { ocorrenciasService } from '../services/ocorrenciasService';
import type { OcorrenciaDetalhe } from '../types/api';
import { urlDaLista } from '../utils/ocorrenciaDeepLink';

const valoresDe = (o: OcorrenciaDetalhe): ValoresOcorrencia => ({
  natureza: o.natureza,
  descricao: o.descricao,
  localizacao: o.localizacao,
  latitude: o.latitude,
  longitude: o.longitude,
  dataHoraFatoLocal: paraInputLocal(new Date(o.data_hora_fato)),
  envolvidos: o.envolvidos.map((e) => ({ nome: e.nome, tipo: e.tipo, documento: e.documento ?? undefined })),
  tipificacoes: o.tipificacoes,
  evidencias: [],
  itensApreendidos: [],
});

export const MinhasOcorrenciasDetalhePage: React.FC = () => {
  const { t } = useTranslation(['ocorrencias', 'common']);
  const { avisar } = useToast();
  const { ocorrenciaId = '' } = useParams();
  const [searchParams] = useSearchParams();
  const [detalhe, setDetalhe] = useState<OcorrenciaDetalhe | null>(null);
  const [editando, setEditando] = useState(false);
  const [ocupado, setOcupado] = useState(false);

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

  const reenviar = async () => {
    if (!detalhe) return;
    setOcupado(true);
    try {
      setDetalhe(await ocorrenciasService.reenviar(detalhe.ocorrencia_id));
      avisar(t('ocorrencias:correcao.reenviada'), 'sucesso');
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    } finally {
      setOcupado(false);
    }
  };

  if (!ocorrenciaId) return <Navigate to="/minhas" replace />;

  return (
    <div className="pagina detalhe-pagina">
      <Link className="btn btn-ghost btn-sm voltar" to={urlDaLista('/minhas', searchParams)}>
        ← {t('ocorrencias:minhas.voltar')}
      </Link>
      <section className="card">
        {!detalhe && <p className="muted">{t('ocorrencias:minhas.selecione')}</p>}
        {detalhe && !editando && (
          <>
            <OcorrenciaDetalheView o={detalhe} onAlterada={() => void carregar()} />
            {detalhe.status === 'EM_CORRECAO' && (
              <div className="acoes">
                <button className="btn" onClick={() => setEditando(true)}>{t('ocorrencias:correcao.editar')}</button>
                <button className="btn btn-primary" disabled={ocupado} onClick={() => void reenviar()}>{t('ocorrencias:correcao.reenviar')}</button>
              </div>
            )}
          </>
        )}
        {detalhe && editando && (
          <>
            <h2>{t('ocorrencias:correcao.titulo', { protocolo: detalhe.numero_protocolo })}</h2>
            {detalhe.justificativa_revisao && <div className="callout"><strong>{t('ocorrencias:detalhe.justificativa')}:</strong> {detalhe.justificativa_revisao}</div>}
            <OcorrenciaForm
              inicial={valoresDe(detalhe)}
              rotuloEnviar={t('ocorrencias:correcao.salvar')}
              ocupado={ocupado}
              onSubmit={async (v) => {
                setOcupado(true);
                try {
                  setDetalhe(await ocorrenciasService.corrigir(detalhe.ocorrencia_id, paraRequest(v)));
                  setEditando(false);
                  avisar(t('ocorrencias:correcao.salva'), 'sucesso');
                } catch (err) {
                  avisar(mensagemDeErro(err), 'erro');
                } finally {
                  setOcupado(false);
                }
              }}
            />
            <button className="btn btn-ghost" onClick={() => setEditando(false)}>{t('common:actions.cancel')}</button>
          </>
        )}
      </section>
    </div>
  );
};
