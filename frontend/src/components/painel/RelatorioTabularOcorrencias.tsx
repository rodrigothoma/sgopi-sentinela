import React from 'react';
import { useTranslation } from 'react-i18next';
import { StatusBadge } from '../StatusBadge';
import type { OcorrenciaResumo } from '../../types/api';

interface Props {
  ocorrencias: OcorrenciaResumo[];
  selecionada: string | null;
  onSelecionar: (id: string) => void;
  onTentarNovamente: () => void;
}

/**
 * Degradação graciosa do painel quando o provedor de mapas não responde
 * (UC05 cenário de exceção I / RNF04).
 *
 * O operador perde o mapa, não a operação: as mesmas ocorrências aparecem em
 * tabela, com endereço e situação, e continuam selecionáveis.
 */
export const RelatorioTabularOcorrencias: React.FC<Props> = ({
  ocorrencias,
  selecionada,
  onSelecionar,
  onTentarNovamente,
}) => {
  const { t } = useTranslation('painel');

  return (
    <div className="alerta erro mapa-indisponivel" role="alert">
      <div className="mapa-indisponivel-topo">
        <div>
          <strong>🗺️ {t('mapa_indisponivel.titulo')}</strong>
          <div className="mapa-indisponivel-subtitulo">{t('mapa_indisponivel.subtitulo')}</div>
        </div>
        <button className="btn btn-sm btn-ghost" onClick={onTentarNovamente}>
          {t('mapa_indisponivel.tentar_novamente')}
        </button>
      </div>

      <div className="mapa-indisponivel-tabela">
        <table className="tabela">
          <thead>
            <tr>
              <th>{t('mapa_indisponivel.col_protocolo')}</th>
              <th>{t('mapa_indisponivel.col_natureza')}</th>
              <th>{t('mapa_indisponivel.col_endereco')}</th>
              <th>{t('mapa_indisponivel.col_status')}</th>
            </tr>
          </thead>
          <tbody>
            {ocorrencias.length === 0 && (
              <tr>
                <td colSpan={4} className="muted">{t('mapa_indisponivel.sem_ocorrencias')}</td>
              </tr>
            )}
            {ocorrencias.map((o) => (
              <tr
                key={o.ocorrencia_id}
                className={selecionada === o.ocorrencia_id ? 'selecionada' : undefined}
                onClick={() => onSelecionar(o.ocorrencia_id)}
              >
                <td><strong>{o.numero_protocolo}</strong></td>
                <td>{o.natureza}</td>
                <td>{o.localizacao}</td>
                <td><StatusBadge status={o.status} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default RelatorioTabularOcorrencias;
