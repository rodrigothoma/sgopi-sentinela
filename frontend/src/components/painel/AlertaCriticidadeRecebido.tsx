import React from 'react';
import { useTranslation } from 'react-i18next';
import { formatarHora } from '../../utils/datas';
import type { NivelCriticidade } from '../../types/api';

export interface AlertaRecebido {
  id: string;
  titulo: string;
  mensagem: string;
  nivel: NivelCriticidade;
  em: string;
}

interface Props {
  alerta: AlertaRecebido;
  onDispensar: () => void;
}

/**
 * Faixa de destaque do alerta de criticidade que chega por WebSocket
 * (UC11 passo 4 e pós-condição 1).
 */
export const AlertaCriticidadeRecebido: React.FC<Props> = ({ alerta, onDispensar }) => {
  const { t } = useTranslation(['painel', 'common']);

  return (
    <div className="alerta erro alerta-criticidade-recebido" role="alert" aria-live="assertive">
      <div className="alerta-criticidade-topo">
        <div>
          <strong className="alerta-criticidade-titulo">
            🚨 {t('painel:alerta_recebido.titulo')} &middot;{' '}
            <span className="alerta-criticidade-nivel">
              {t(`painel:alerta.criticidade.${alerta.nivel}`, { defaultValue: alerta.nivel })}
            </span>
          </strong>
          <div className="alerta-criticidade-assunto">{alerta.titulo}</div>
          <div className="alerta-criticidade-mensagem">{alerta.mensagem}</div>
          <div className="alerta-criticidade-hora">
            {t('painel:alerta_recebido.recebido_em', { hora: formatarHora(alerta.em) })}
          </div>
        </div>
        <button className="btn btn-sm btn-ghost" onClick={onDispensar}>
          {t('painel:alerta_recebido.dispensar')}
        </button>
      </div>
    </div>
  );
};

export default AlertaCriticidadeRecebido;
