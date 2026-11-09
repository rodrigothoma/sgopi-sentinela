import React from 'react';
import { useTranslation } from 'react-i18next';
import type { StatusSimuladorCompleto } from '../../types/api';

interface ControleSimuladorProps {
  podeDespachar: boolean;
  simulador: StatusSimuladorCompleto | null;
  onAlternar: () => Promise<void>;
}

/** Apresenta o controle e os contadores; consultas e ações continuam coordenadas pela página. */
export const ControleSimulador: React.FC<ControleSimuladorProps> = ({ podeDespachar, simulador, onAlternar }) => {
  const { t } = useTranslation('painel');
  return (
    <>
      {podeDespachar && simulador && (
        <button className={`btn ${simulador.ligado ? 'btn-warn' : 'btn-primary'}`} onClick={onAlternar}>
          {simulador.ligado ? t('painel:simulador.desligar') : t('painel:simulador.ligar')} ({simulador.ticks})
        </button>
      )}
      {podeDespachar && simulador?.orquestrador?.ligado && (
        <span className="badge badge-OK">
          {t('painel:simulador.despacho_auto')} · {t('painel:simulador.despacho_contador', { despachados: simulador.orquestrador.despachados, encerrados: simulador.orquestrador.encerrados })}
        </span>
      )}
    </>
  );
};
