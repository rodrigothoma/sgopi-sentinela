import React from 'react';
import { useTranslation } from 'react-i18next';
import { StatusBadge } from '../StatusBadge';
import { formatarNatureza } from '../../utils/formatarNatureza';
import type { ConsultaPublicaResponse } from '../../services/api';

const STATUS_ETAPAS = [
  { id: 'AGUARDANDO_REVISAO', rotuloChave: 'triagem' },
  { id: 'VALIDADA', rotuloChave: 'validada' },
  { id: 'EM_ATENDIMENTO', rotuloChave: 'atendimento' },
  { id: 'ENCERRADA', rotuloChave: 'finalizada' },
];

const etapaAtual = (status: string): number => {
  if (status === 'AGUARDANDO_REVISAO' || status === 'EM_CORRECAO') return 0;
  if (status === 'VALIDADA' || status === 'EM_DESPACHO') return 1;
  if (status === 'EM_ATENDIMENTO') return 2;
  if (status === 'ENCERRADA' || status === 'REJEITADA') return 3;
  return 0;
};

interface Props {
  dados: ConsultaPublicaResponse;
}

/** Acompanhamento público da ocorrência pelo número de protocolo: linha do tempo + dados não sensíveis (RNF02). */
export const ResultadoProtocolo: React.FC<Props> = ({ dados }) => {
  const { t, i18n } = useTranslation(['publico']);
  const localeData = i18n.language && i18n.language.startsWith('en') ? 'en-US' : 'pt-BR';
  const atualIdx = etapaAtual(dados.status);

  return (
    <div className="resultado-publico">
      <div className="resultado-publico-cabecalho">
        <div>
          <span className="small muted">{t('publico:consulta.protocolo_rotulo')}</span>
          <div className="resultado-publico-codigo">{dados.numero_protocolo}</div>
        </div>
        <StatusBadge status={dados.status} />
      </div>

      <div className="status-timeline">
        {STATUS_ETAPAS.map((etapa, idx) => {
          const concluida = idx < atualIdx;
          const ativa = idx === atualIdx;
          return (
            <div
              key={etapa.id}
              className={`timeline-step ${ativa ? 'active' : ''} ${concluida ? 'completed' : ''}`}
            >
              <div className="timeline-dot">{concluida ? '✓' : idx + 1}</div>
              <div className="timeline-label">{t(`publico:consulta.etapas.${etapa.rotuloChave}`)}</div>
            </div>
          );
        })}
      </div>

      <dl className="grid2" style={{ marginTop: 24 }}>
        <dt>{t('publico:consulta.detalhes.natureza')}</dt>
        <dd><strong>{formatarNatureza(dados.natureza, t)}</strong></dd>

        <dt>{t('publico:consulta.detalhes.local')}</dt>
        <dd>{dados.localizacao}</dd>

        <dt>{t('publico:consulta.detalhes.data_abertura')}</dt>
        <dd>{new Date(dados.criada_em).toLocaleString(localeData)}</dd>

        {dados.desfecho && (
          <>
            <dt>{t('publico:consulta.detalhes.desfecho')}</dt>
            <dd>{dados.desfecho}</dd>
          </>
        )}
      </dl>
    </div>
  );
};
