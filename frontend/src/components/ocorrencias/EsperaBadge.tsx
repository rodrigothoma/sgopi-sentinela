import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { formatarEspera } from '../../utils/duracao';

/** Horas de espera a partir das quais a triagem passa a ser sinalizada. */
export const ESPERA_ATENCAO_HORAS = 4;
export const ESPERA_CRITICA_HORAS = 24;

const MS_POR_HORA = 3_600_000;
/** Só faz sentido contar espera enquanto a ocorrência depende de uma decisão. */
const STATUS_EM_ESPERA = ['AGUARDANDO_REVISAO', 'EM_CORRECAO'];

interface Props {
  /** Instante inicial da contagem (criação da ocorrência). */
  desde: string;
  status: string;
}

/**
 * Há quanto tempo a ocorrência aguarda decisão.
 *
 * A fila já ordena por gravidade e antiguidade, mas não mostrava a espera: o
 * Delegado via a ordem, não o tempo. Recalcula sozinho a cada minuto.
 */
export const EsperaBadge: React.FC<Props> = ({ desde, status }) => {
  const { t } = useTranslation('ocorrencias');
  const [agora, setAgora] = useState(() => Date.now());

  useEffect(() => {
    const id = window.setInterval(() => setAgora(Date.now()), 60_000);
    return () => window.clearInterval(id);
  }, []);

  if (!STATUS_EM_ESPERA.includes(status)) return null;

  const inicio = new Date(desde).getTime();
  if (Number.isNaN(inicio)) return null;

  const decorridoMs = Math.max(0, agora - inicio);
  const horas = decorridoMs / MS_POR_HORA;

  const cor =
    horas >= ESPERA_CRITICA_HORAS ? 'var(--danger)' : horas >= ESPERA_ATENCAO_HORAS ? 'var(--warn)' : 'var(--muted)';
  const fundo =
    horas >= ESPERA_CRITICA_HORAS
      ? 'rgba(239, 68, 68, 0.15)'
      : horas >= ESPERA_ATENCAO_HORAS
        ? 'rgba(245, 158, 11, 0.15)'
        : 'transparent';

  return (
    <span
      title={t('fila.espera_titulo', { defaultValue: 'Tempo aguardando decisão' })}
      style={{
        padding: '0.15rem 0.45rem',
        borderRadius: '4px',
        background: fundo,
        color: cor,
        fontSize: '0.75rem',
        fontWeight: 700,
        whiteSpace: 'nowrap',
      }}
    >
      {horas >= ESPERA_ATENCAO_HORAS ? '⏱ ' : ''}
      {t('fila.espera', {
        defaultValue: 'há {{tempo}}',
        tempo: formatarEspera(Math.round(decorridoMs / 1000)),
      })}
    </span>
  );
};

export default EsperaBadge;
