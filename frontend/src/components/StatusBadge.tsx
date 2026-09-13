import React from 'react';
import { useTranslation } from 'react-i18next';

export const StatusBadge: React.FC<{ status: string; grupo?: 'status' | 'situacao' | 'sinal' }> = ({ status, grupo = 'status' }) => {
  const { t } = useTranslation('common');
  return <span className={`badge badge-${status}`}>{t(`${grupo}.${status}`, status)}</span>;
};
