import React from 'react';
import { useTranslation } from 'react-i18next';
import type { PrioridadeOcorrencia } from '../types/api';

/** Gravidade da ocorrência (sugestão #7): texto + cor, nunca só a cor. */
export const PrioridadeBadge: React.FC<{ prioridade?: PrioridadeOcorrencia | null }> = ({ prioridade }) => {
  const { t } = useTranslation('common');
  if (!prioridade) return null;
  return (
    <span className={`badge badge-prioridade badge-prioridade-${prioridade}`} title={t('prioridade.titulo')}>
      {t(`prioridade.${prioridade}`)}
    </span>
  );
};
