import React, { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { OcorrenciaDetalheView } from '../components/ocorrencias/OcorrenciaDetalhe';
import { OcorrenciaForm, paraInputLocal, paraRequest, type ValoresOcorrencia } from '../components/ocorrencias/OcorrenciaForm';
import { StatusBadge } from '../components/StatusBadge';
import { useToast } from '../hooks/useToast';
import { mensagemDeErro } from '../services/api';
import { ocorrenciasService } from '../services/ocorrenciasService';
import type { OcorrenciaDetalhe, OcorrenciaResumo } from '../types/api';

/** Agente: minhas ocorrências + correção/reenvio das devolvidas (RF14). */
export const MinhasOcorrenciasPage: React.FC = () => {
  const { t } = useTranslation(['ocorrencias', 'common']);
  const { avisar } = useToast();
  const [itens, setItens] = useState<OcorrenciaResumo[]>([]);
  const [detalhe, setDetalhe] = useState<OcorrenciaDetalhe | null>(null);
  const [editando, setEditando] = useState(false);
  const [ocupado, setOcupado] = useState(false);

  const carregar = useCallback(async () => {
    try {
      setItens((await ocorrenciasService.listar([], 100)).itens.slice().reverse());
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    }
  }, [avisar]);

  useEffect(() => {
    carregar();
  }, [carregar]);

  const abrir = async (id: string) => {
    setEditando(false);
    setDetalhe(await ocorrenciasService.buscarPorId(id));
  };

  const valoresDe = (o: OcorrenciaDetalhe): ValoresOcorrencia => ({
    natureza: o.natureza, descricao: o.descricao, localizacao: o.localizacao, latitude: o.latitude, longitude: o.longitude,
    dataHoraFatoLocal: paraInputLocal(new Date(o.data_hora_fato)),
    envolvidos: o.envolvidos.map((e) => ({ nome: e.nome, tipo: e.tipo, documento: e.documento ?? undefined })),
    tipificacoes: o.tipificacoes, evidencias: [],
  });

  const reenviar = async () => {
    if (!detalhe) return;
    setOcupado(true);
    try {
      setDetalhe(await ocorrenciasService.reenviar(detalhe.ocorrencia_id));
      avisar(t('ocorrencias:correcao.reenviada'), 'sucesso');
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
        <h2>{t('ocorrencias:minhas.titulo')}</h2>
        {itens.length === 0 && <p className="muted">{t('ocorrencias:minhas.vazio')}</p>}
        <ul className="lista clicavel">
          {itens.map((o) => (
            <li key={o.ocorrencia_id} className={detalhe?.ocorrencia_id === o.ocorrencia_id ? 'ativo' : ''} onClick={() => abrir(o.ocorrencia_id)}>
              <span><strong>{o.numero_protocolo}</strong> · {o.natureza}</span>
              <StatusBadge status={o.status} />
            </li>
          ))}
        </ul>
      </section>
      <section className="card">
        {!detalhe && <p className="muted">{t('ocorrencias:minhas.selecione')}</p>}
        {detalhe && !editando && (
          <>
            <OcorrenciaDetalheView o={detalhe} />
            {detalhe.status === 'EM_CORRECAO' && (
              <div className="acoes">
                <button className="btn" onClick={() => setEditando(true)}>{t('ocorrencias:correcao.editar')}</button>
                <button className="btn btn-primary" disabled={ocupado} onClick={reenviar}>{t('ocorrencias:correcao.reenviar')}</button>
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
