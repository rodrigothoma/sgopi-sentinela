import React from 'react';
import { useTranslation } from 'react-i18next';
import { useRelogioMinuto } from '../../hooks/useRelogioMinuto';
import { calcularEspera } from '../../utils/espera';
import type { StatusOcorrencia } from '../../types/api';

interface Props {
  /** Instante inicial da contagem (criação da ocorrência). */
  desde: string;
  status: StatusOcorrencia;
}

/**
 * Há quanto tempo a ocorrência aguarda decisão.
 *
 * A fila já ordena por gravidade e antiguidade, mas não mostrava a espera: o
 * Delegado via a ordem, não o tempo. A regra está em ``calcularEspera``; aqui
 * fica só a apresentação.
 */
export const EsperaBadge: React.FC<Props> = ({ desde, status }) => {
  const { t } = useTranslation('ocorrencias');
  const agora = useRelogioMinuto();

  const espera = calcularEspera(desde, status, agora);
  if (!espera) return null;

  return (
    <span
      className={`espera-badge espera-${espera.nivel}`}
      title={t('fila.espera_titulo', { defaultValue: 'Tempo aguardando decisão' })}
    >
      {espera.nivel !== 'normal' && '⏱ '}
      {t('fila.espera', { defaultValue: 'há {{tempo}}', tempo: espera.texto })}
    </span>
  );
};

export default EsperaBadge;
