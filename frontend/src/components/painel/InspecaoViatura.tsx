import React from 'react';
import { useTranslation } from 'react-i18next';
import type { Viatura } from '../../types/api';
import { formatarDataHora } from '../../utils/datas';
import { posicaoDaViatura } from '../../utils/inspecaoViatura';
import { StatusBadge } from '../StatusBadge';

interface Props {
  viatura: Viatura;
  mapaDisponivel: boolean;
  onCentralizar: () => void;
  onFechar: () => void;
}

/** Apresenta o objeto atual da frota; não mantém uma cópia nem abre outra assinatura de telemetria. */
export const InspecaoViatura: React.FC<Props> = ({ viatura, mapaDisponivel, onCentralizar, onFechar }) => {
  const { t } = useTranslation('painel');
  const posicao = posicaoDaViatura(viatura);
  const instante = viatura.posicao_registrada_em;
  const ultimaPosicao = instante && Number.isFinite(Date.parse(instante)) ? formatarDataHora(instante) : t('inspecao.sem_registro');
  const motivo = !posicao ? t('inspecao.sem_posicao') : !mapaDisponivel ? t('inspecao.mapa_indisponivel') : null;

  return (
    <section className="card inspecao-viatura" data-cy="inspecao-viatura" aria-labelledby="inspecao-viatura-titulo">
      <div className="inspecao-viatura-cabecalho">
        <div><span className="inspecao-viatura-rotulo">{t('inspecao.titulo')}</span><h3 id="inspecao-viatura-titulo">{viatura.prefixo}</h3></div>
        <button type="button" className="btn btn-ghost btn-sm" onClick={onFechar} data-cy="fechar-inspecao">{t('inspecao.fechar')}</button>
      </div>
      <div className="lista-badges"><StatusBadge status={viatura.situacao} grupo="situacao" /><StatusBadge status={viatura.sinal} grupo="sinal" /></div>
      <dl className="inspecao-viatura-dados">
        <div><dt>{t('inspecao.placa')}</dt><dd>{viatura.placa}</dd></div>
        <div><dt>{t('inspecao.responsavel')}</dt><dd data-cy="inspecao-responsavel">{viatura.responsavel || t('inspecao.sem_responsavel')}</dd></div>
        <div><dt>{t('inspecao.coordenadas')}</dt><dd data-cy="inspecao-coordenadas">{posicao ? posicao.map((valor) => valor.toFixed(5)).join(', ') : t('inspecao.sem_posicao')}</dd></div>
        <div><dt>{t('inspecao.ultima_posicao')}</dt><dd>{ultimaPosicao}</dd></div>
      </dl>
      {posicao && viatura.sinal !== 'OK' && <p className="inspecao-viatura-aviso">{t('inspecao.posicao_desatualizada')}</p>}
      {motivo && <p id="inspecao-motivo" className="muted small">{motivo}</p>}
      <button type="button" className="btn btn-primary btn-sm" disabled={!!motivo} aria-describedby={motivo ? 'inspecao-motivo' : undefined} onClick={onCentralizar} data-cy="centralizar-viatura">{t('inspecao.centralizar')}</button>
    </section>
  );
};
