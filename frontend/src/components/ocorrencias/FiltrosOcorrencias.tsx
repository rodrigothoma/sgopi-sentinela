import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import type { FiltrosOcorrencias, OrigemOcorrencia } from '../../types/api';
import { temFiltroAtivo } from '../../utils/filtrosOcorrencias';

interface Props {
  valor: FiltrosOcorrencias;
  onAplicar: (filtros: FiltrosOcorrencias) => void;
  /** A origem só faz sentido para quem vê comunicações do cidadão (fila do Delegado). */
  mostrarOrigem?: boolean;
}

const MAXIMO_TERMO = 200;

/** Barra de busca reutilizável da fila do Delegado e de "Minhas ocorrências" (RF01/RF04). */
export const FiltrosOcorrenciasBar: React.FC<Props> = ({ valor, onAplicar, mostrarOrigem = false }) => {
  const { t } = useTranslation('ocorrencias');
  const [rascunho, setRascunho] = useState<FiltrosOcorrencias>(valor);
  const avancadosAtivos = temFiltroAtivo({ ...valor, texto: undefined });

  useEffect(() => setRascunho(valor), [valor]);

  const campo = (chave: keyof FiltrosOcorrencias) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setRascunho((atual) => ({ ...atual, [chave]: e.target.value || undefined }));

  const enviar = (e: React.FormEvent) => {
    e.preventDefault();
    onAplicar(rascunho);
  };

  return (
    <form className="filtros-ocorrencias" onSubmit={enviar} role="search">
      <div className="filtros-ocorrencias-linha">
        <input
          type="search"
          aria-label={t('filtros.texto')}
          placeholder={t('filtros.texto_placeholder')}
          maxLength={MAXIMO_TERMO}
          value={rascunho.texto ?? ''}
          onChange={campo('texto')}
        />
        <button type="submit" className="btn btn-primary btn-sm">{t('filtros.buscar')}</button>
        {temFiltroAtivo(valor) && (
          <button type="button" className="btn btn-ghost btn-sm" onClick={() => onAplicar({})}>{t('filtros.limpar')}</button>
        )}
      </div>
      <details open={avancadosAtivos || undefined}>
        <summary className="muted small">{t('filtros.mais')}</summary>
        <div className="filtros-ocorrencias-grade">
          <label>{t('filtros.protocolo')}
            <input maxLength={MAXIMO_TERMO} value={rascunho.protocolo ?? ''} onChange={campo('protocolo')} />
          </label>
          <label>{t('filtros.natureza')}
            <input maxLength={MAXIMO_TERMO} value={rascunho.natureza ?? ''} onChange={campo('natureza')} />
          </label>
          <label>{t('filtros.data_de')}
            <input type="date" value={rascunho.dataFatoDe ?? ''} max={rascunho.dataFatoAte} onChange={campo('dataFatoDe')} />
          </label>
          <label>{t('filtros.data_ate')}
            <input type="date" value={rascunho.dataFatoAte ?? ''} min={rascunho.dataFatoDe} onChange={campo('dataFatoAte')} />
          </label>
          {mostrarOrigem && (
            <label>{t('filtros.origem')}
              <select value={rascunho.origem ?? ''} onChange={campo('origem')}>
                <option value="">{t('filtros.origem_todas')}</option>
                {(['POLICIAL', 'PUBLICA'] as OrigemOcorrencia[]).map((o) => (
                  <option key={o} value={o}>{t(`filtros.origem_${o}`)}</option>
                ))}
              </select>
            </label>
          )}
        </div>
      </details>
    </form>
  );
};
