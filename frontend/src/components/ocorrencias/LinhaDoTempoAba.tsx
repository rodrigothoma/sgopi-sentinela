import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { mensagemDeErro } from '../../services/api';
import { ocorrenciasService } from '../../services/ocorrenciasService';
import type { EventoLinhaDoTempo } from '../../types/api';
import { formatarDataHora } from '../../utils/datas';
import { StatusBadge } from '../StatusBadge';

interface Props {
  ocorrenciaId: string;
  /** Muda a cada alteração da ocorrência: recarrega a linha do tempo junto com o detalhe. */
  versao: number;
}

const Detalhe: React.FC<{ e: EventoLinhaDoTempo }> = ({ e }) => {
  const { t } = useTranslation(['ocorrencias', 'common']);
  const d = e.detalhes;
  switch (e.tipo) {
    case 'STATUS':
      return (
        <>
          {d.de ? <StatusBadge status={String(d.de)} /> : null}
          {d.de ? ' → ' : null}
          <StatusBadge status={String(d.para)} />
          {d.justificativa ? <p className="linha-tempo-texto">{String(d.justificativa)}</p> : null}
        </>
      );
    case 'INTEGRIDADE_VERIFICADA':
      return <>{String(d.nome)} · <span className={d.integridade === 'INTEGRA' ? 'ok' : 'erro'}>{t(`ocorrencias:linha_tempo.integridade_${String(d.integridade)}`, String(d.integridade))}</span></>;
    case 'CUSTODIA_MOVIMENTADA':
      return <>{String(d.numero_lacre)} · {d.origem ? `${String(d.origem)} → ` : ''}{String(d.destino)}</>;
    case 'DESPACHO':
    case 'ORDEM_ENCERRADA':
      return <>{String(d.numero)}{d.viatura ? ` · ${String(d.viatura)}` : ''}{d.apoio ? ` · ${t('ocorrencias:linha_tempo.apoio')}` : ''}</>;
    case 'ITEM_APREENDIDO':
      return <>{String(d.descricao)} · {t('ocorrencias:linha_tempo.lacre')} {String(d.numero_lacre)}</>;
    case 'EVIDENCIA_ANEXADA':
      return <>{String(d.nome)} · <code>{String(d.hash_sha256).slice(0, 12)}…</code></>;
    default:
      return <>{String(d.numero ?? '')}{d.tipo_pericia ? ` · ${String(d.tipo_pericia)}` : ''}</>;
  }
};

/** Sugestão #12: tudo o que aconteceu com a ocorrência, em ordem cronológica. */
export const LinhaDoTempoAba: React.FC<Props> = ({ ocorrenciaId, versao }) => {
  const { t } = useTranslation(['ocorrencias', 'common']);
  const [eventos, setEventos] = useState<EventoLinhaDoTempo[] | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    let ativo = true;
    setErro(null);
    ocorrenciasService
      .linhaDoTempo(ocorrenciaId)
      .then((r) => ativo && setEventos(r))
      .catch((err) => ativo && setErro(mensagemDeErro(err)));
    return () => { ativo = false; };
  }, [ocorrenciaId, versao]);

  if (erro) return <p className="erro">{erro}</p>;
  if (!eventos) return <p className="muted">{t('common:actions.loading')}</p>;
  if (eventos.length === 0) return <p className="muted">{t('ocorrencias:linha_tempo.vazia')}</p>;
  return (
    <ol className="linha-tempo">
      {eventos.map((e, i) => (
        <li key={`${e.tipo}-${e.em}-${i}`} className={`linha-tempo-item linha-tempo-${e.tipo}`}>
          <div className="linha-tempo-cabecalho">
            <strong>{t(`ocorrencias:linha_tempo.tipos.${e.tipo}`)}</strong>
            <time dateTime={e.em} className="muted small">{formatarDataHora(e.em)}</time>
          </div>
          <div className="linha-tempo-corpo"><Detalhe e={e} /></div>
          {e.por_nome && <small className="muted">{t('ocorrencias:linha_tempo.por', { nome: e.por_nome })}</small>}
        </li>
      ))}
    </ol>
  );
};
