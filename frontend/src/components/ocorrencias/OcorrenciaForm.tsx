import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { EnvolvidoForm } from './EnvolvidoForm';
import { TipificacaoForm } from './TipificacaoForm';
import { SeletorCoordenada } from '../painel/SeletorCoordenada';
import type { EnvolvidoDTO, RegistrarOcorrenciaRequest, TipificacaoDTO } from '../../types/api';

export interface ValoresOcorrencia {
  natureza: string; descricao: string; localizacao: string;
  latitude: number | null; longitude: number | null; dataHoraFatoLocal: string;
  envolvidos: EnvolvidoDTO[]; tipificacoes: TipificacaoDTO[];
}

export const valoresVazios = (): ValoresOcorrencia => ({
  natureza: '', descricao: '', localizacao: '', latitude: null, longitude: null,
  dataHoraFatoLocal: paraInputLocal(new Date()), envolvidos: [], tipificacoes: [],
});

export function paraInputLocal(d: Date): string {
  const p = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`;
}

export function paraRequest(v: ValoresOcorrencia): RegistrarOcorrenciaRequest {
  return {
    natureza: v.natureza.trim(), descricao: v.descricao.trim(), localizacao: v.localizacao.trim(),
    latitude: v.latitude as number, longitude: v.longitude as number,
    data_hora_fato: new Date(v.dataHoraFatoLocal).toISOString(),
    envolvidos: v.envolvidos, tipificacoes: v.tipificacoes,
  };
}

interface Props {
  inicial: ValoresOcorrencia;
  onSubmit: (v: ValoresOcorrencia) => Promise<void>;
  rotuloEnviar: string;
  ocupado: boolean;
}

export const OcorrenciaForm: React.FC<Props> = ({ inicial, onSubmit, rotuloEnviar, ocupado }) => {
  const { t } = useTranslation(['ocorrencias', 'common']);
  const [v, setV] = useState<ValoresOcorrencia>(inicial);
  const [erro, setErro] = useState<string | null>(null);
  const set = <K extends keyof ValoresOcorrencia>(k: K, val: ValoresOcorrencia[K]) => setV((x) => ({ ...x, [k]: val }));

  const validar = (): string | null => {
    if (!v.natureza.trim() || !v.localizacao.trim()) return t('ocorrencias:erros.campos_obrigatorios');
    if (v.descricao.trim().length < 20) return t('ocorrencias:erros.descricao_curta');
    if (v.latitude === null || v.longitude === null) return t('ocorrencias:erros.sem_coordenada');
    if (new Date(v.dataHoraFatoLocal).getTime() > Date.now()) return t('ocorrencias:erros.data_futura');
    if (v.envolvidos.length === 0) return t('ocorrencias:erros.sem_envolvidos');
    return null;
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    const problema = validar();
    setErro(problema);
    if (problema) return;
    await onSubmit(v);
  };

  return (
    <form onSubmit={submit} className="form">
      {erro && <div className="alerta erro">{erro}</div>}
      <div className="grid2">
        <label>
          {t('ocorrencias:form.natureza_label')}
          <input value={v.natureza} onChange={(e) => set('natureza', e.target.value)} placeholder={t('ocorrencias:form.natureza_placeholder')} />
        </label>
        <label>
          {t('ocorrencias:form.data_hora_fato_label')}
          <input type="datetime-local" value={v.dataHoraFatoLocal} max={paraInputLocal(new Date())} onChange={(e) => set('dataHoraFatoLocal', e.target.value)} />
        </label>
      </div>
      <label>
        {t('ocorrencias:form.localizacao_label')}
        <input value={v.localizacao} onChange={(e) => set('localizacao', e.target.value)} placeholder={t('ocorrencias:form.localizacao_placeholder')} />
      </label>
      <label>
        {t('ocorrencias:form.coordenada_label')} <span className="muted">{t('ocorrencias:form.coordenada_ajuda')}</span>
      </label>
      <SeletorCoordenada latitude={v.latitude} longitude={v.longitude} onChange={(lat, lon) => setV((x) => ({ ...x, latitude: lat, longitude: lon }))} />
      <label>
        {t('ocorrencias:form.descricao_label')} <span className="muted">({v.descricao.trim().length}/20+)</span>
        <textarea rows={5} value={v.descricao} onChange={(e) => set('descricao', e.target.value)} placeholder={t('ocorrencias:form.descricao_placeholder')} />
      </label>

      <fieldset>
        <legend>{t('ocorrencias:form.envolvidos_label')} *</legend>
        <EnvolvidoForm onAdd={(env) => set('envolvidos', [...v.envolvidos, env])} />
        <ul className="lista">
          {v.envolvidos.map((item, idx) => (
            <li key={idx}>
              <span><strong>{item.nome}</strong> · {t(`ocorrencias:envolvido.${item.tipo}`)}{item.documento ? ` · ${item.documento}` : ''}</span>
              <button type="button" className="btn btn-link" onClick={() => set('envolvidos', v.envolvidos.filter((_, i) => i !== idx))}>{t('common:actions.remover')}</button>
            </li>
          ))}
        </ul>
      </fieldset>

      <fieldset>
        <legend>{t('ocorrencias:form.tipificacoes_label')}</legend>
        <TipificacaoForm onAdd={(tp) => set('tipificacoes', [...v.tipificacoes, tp])} />
        <ul className="lista">
          {v.tipificacoes.map((item, idx) => (
            <li key={idx}>
              <span><strong>{item.artigo}</strong> — {item.descricao}</span>
              <button type="button" className="btn btn-link" onClick={() => set('tipificacoes', v.tipificacoes.filter((_, i) => i !== idx))}>{t('common:actions.remover')}</button>
            </li>
          ))}
        </ul>
      </fieldset>

      <button type="submit" className="btn btn-primary" disabled={ocupado}>
        {ocupado ? t('common:actions.loading') : rotuloEnviar}
      </button>
    </form>
  );
};
