import React from 'react';
import { useTranslation } from 'react-i18next';
import type { OcorrenciaDetalhe as Detalhe } from '../../types/api';
import { StatusBadge } from '../StatusBadge';

const fmt = (iso: string) => new Date(iso).toLocaleString();

export const OcorrenciaDetalheView: React.FC<{ o: Detalhe }> = ({ o }) => {
  const { t } = useTranslation(['ocorrencias', 'common']);
  return (
    <div className="detalhe">
      <div className="detalhe-cabecalho">
        <h2>
          {o.numero_protocolo} <StatusBadge status={o.status} />
        </h2>
        <span className="muted">
          {t('ocorrencias:detalhe.versao')} {o.versao} · {t('ocorrencias:detalhe.registrada_em')} {fmt(o.criada_em)}
        </span>
      </div>
      <dl className="grid2">
        <dt>{t('ocorrencias:form.natureza_label')}</dt><dd>{o.natureza}</dd>
        <dt>{t('ocorrencias:form.data_hora_fato_label')}</dt><dd>{fmt(o.data_hora_fato)}</dd>
        <dt>{t('ocorrencias:form.localizacao_label')}</dt><dd>{o.localizacao}</dd>
        <dt>{t('ocorrencias:form.coordenada_label')}</dt><dd>{o.latitude.toFixed(5)}, {o.longitude.toFixed(5)}</dd>
      </dl>
      <h4>{t('ocorrencias:form.descricao_label')}</h4>
      <p className="narrativa">{o.descricao}</p>
      {o.narrativa_integra !== null && (
        <p className={o.narrativa_integra ? 'ok' : 'erro'}>
          {o.narrativa_integra ? t('ocorrencias:detalhe.integra') : t('ocorrencias:detalhe.adulterada')} · SHA-256 {o.hash_narrativa?.slice(0, 12)}…
        </p>
      )}
      {o.justificativa_revisao && (
        <div className="callout">
          <strong>{t('ocorrencias:detalhe.justificativa')}:</strong> {o.justificativa_revisao}
        </div>
      )}
      {o.desfecho && (
        <div className="callout">
          <strong>{t('ocorrencias:detalhe.desfecho')}:</strong> {o.desfecho}
        </div>
      )}
      <h4>{t('ocorrencias:form.envolvidos_label')}</h4>
      <ul className="lista">
        {o.envolvidos.map((e) => (
          <li key={e.id}>
            <strong>{e.nome}</strong> · {t(`ocorrencias:envolvido.${e.tipo}`)}
            {e.documento ? ` · ${e.documento}` : ''}
          </li>
        ))}
      </ul>
      {o.tipificacoes.length > 0 && (
        <>
          <h4>{t('ocorrencias:form.tipificacoes_label')}</h4>
          <ul className="lista">
            {o.tipificacoes.map((tp, i) => (
              <li key={i}><strong>{tp.artigo}</strong> — {tp.descricao}</li>
            ))}
          </ul>
        </>
      )}
      <h4>{t('ocorrencias:detalhe.historico')}</h4>
      <ol className="historico">
        {o.historico_status.map((h, i) => (
          <li key={i}>
            <span className="muted">{fmt(h.em)}</span> {h.de ? <><StatusBadge status={h.de} /> → </> : null}
            <StatusBadge status={h.para} />
            {h.justificativa && <em> — {h.justificativa}</em>}
          </li>
        ))}
      </ol>
    </div>
  );
};
