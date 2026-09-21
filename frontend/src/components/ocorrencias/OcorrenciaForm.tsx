import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { EnvolvidoForm } from './EnvolvidoForm';
import { LocalOcorrencia } from './LocalOcorrencia';
import { TipificacaoForm } from './TipificacaoForm';
import type { EnvolvidoDTO, RegistrarOcorrenciaRequest, TipificacaoDTO } from '../../types/api';

export interface ValoresOcorrencia {
  natureza: string; descricao: string; localizacao: string;
  latitude: number | null; longitude: number | null; dataHoraFatoLocal: string;
  envolvidos: EnvolvidoDTO[]; tipificacoes: TipificacaoDTO[]; evidencias: File[];
}

export const valoresVazios = (): ValoresOcorrencia => ({
  natureza: '', descricao: '', localizacao: '', latitude: null, longitude: null,
  dataHoraFatoLocal: paraInputLocal(new Date()), envolvidos: [], tipificacoes: [], evidencias: [],
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
  permitirEvidencias?: boolean;
}

const FORMATOS_EVIDENCIA = ['application/pdf', 'image/jpeg', 'image/png'];
const TAMANHO_MAXIMO_EVIDENCIA = 10 * 1024 * 1024;
const MINIMO_DESCRICAO = 20;

export const OcorrenciaForm: React.FC<Props> = ({ inicial, onSubmit, rotuloEnviar, ocupado, permitirEvidencias = false }) => {
  const { t } = useTranslation(['ocorrencias', 'common']);
  const [v, setV] = useState<ValoresOcorrencia>(inicial);
  const [erro, setErro] = useState<string | null>(null);
  const set = <K extends keyof ValoresOcorrencia>(k: K, val: ValoresOcorrencia[K]) => setV((x) => ({ ...x, [k]: val }));

  const validar = (): string | null => {
    if (!v.natureza.trim() || !v.localizacao.trim()) return t('ocorrencias:erros.campos_obrigatorios');
    if (v.descricao.trim().length < MINIMO_DESCRICAO) return t('ocorrencias:erros.descricao_curta');
    if (v.latitude === null || v.longitude === null) return t('ocorrencias:erros.sem_coordenada');
    if (new Date(v.dataHoraFatoLocal).getTime() > Date.now()) return t('ocorrencias:erros.data_futura');
    if (v.envolvidos.length === 0) return t('ocorrencias:erros.sem_envolvidos');
    if (v.evidencias.length > 10) return t('ocorrencias:evidencias.limite');
    if (v.evidencias.some((arquivo) => !FORMATOS_EVIDENCIA.includes(arquivo.type))) return t('ocorrencias:evidencias.formato_invalido');
    if (v.evidencias.some((arquivo) => arquivo.size > TAMANHO_MAXIMO_EVIDENCIA)) return t('ocorrencias:evidencias.tamanho_excedido');
    return null;
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    const problema = validar();
    setErro(problema);
    if (problema) {
      window.scrollTo({ top: 0, behavior: 'smooth' });
      return;
    }
    await onSubmit(v);
  };

  const descricaoLen = v.descricao.trim().length;

  return (
    <form onSubmit={submit} className="form" noValidate>
      {erro && <div className="alerta erro" role="alert">{erro}</div>}

      <section className="secao">
        <h3>{t('ocorrencias:form.secao_fato')}</h3>
        <div className="grid2">
          <label htmlFor="natureza">
            {t('ocorrencias:form.natureza_label')} <span className="obrigatorio">*</span>
            <input id="natureza" value={v.natureza} maxLength={255} onChange={(e) => set('natureza', e.target.value)} placeholder={t('ocorrencias:form.natureza_placeholder')} />
          </label>
          <label htmlFor="data-hora-fato">
            {t('ocorrencias:form.data_hora_fato_label')} <span className="obrigatorio">*</span>
            <input id="data-hora-fato" type="datetime-local" value={v.dataHoraFatoLocal} max={paraInputLocal(new Date())} onChange={(e) => set('dataHoraFatoLocal', e.target.value)} />
          </label>
        </div>
      </section>

      <section className="secao">
        <h3>{t('ocorrencias:form.secao_local')}</h3>
        <LocalOcorrencia
          valor={{ localizacao: v.localizacao, latitude: v.latitude, longitude: v.longitude }}
          onChange={(patch) => setV((x) => ({ ...x, ...patch }))}
        />
      </section>

      <section className="secao">
        <h3>{t('ocorrencias:form.secao_narrativa')}</h3>
        <label htmlFor="descricao">
          {t('ocorrencias:form.descricao_label')} <span className="obrigatorio">*</span>{' '}
          <span className={`contador ${descricaoLen < MINIMO_DESCRICAO ? 'obrigatorio' : 'muted'}`}>
            ({descricaoLen}/{MINIMO_DESCRICAO}+ · {t('ocorrencias:form.descricao_ajuda')})
          </span>
          <textarea id="descricao" rows={6} value={v.descricao} onChange={(e) => set('descricao', e.target.value)} placeholder={t('ocorrencias:form.descricao_placeholder')} />
        </label>
      </section>

      <fieldset>
        <legend>{t('ocorrencias:form.envolvidos_label')} <span className="obrigatorio">*</span></legend>
        <EnvolvidoForm onAdd={(env) => set('envolvidos', [...v.envolvidos, env])} />
        {v.envolvidos.length === 0 && <p className="muted small">{t('ocorrencias:erros.sem_envolvidos')}</p>}
        <ul className="lista">
          {v.envolvidos.map((item, idx) => (
            <li key={idx}>
              <span>
                <strong>{item.nome}</strong> · {t(`ocorrencias:envolvido.${item.tipo}`)}
                {item.documento ? ` · ${item.documento}` : ` · ${t('ocorrencias:envolvido.documento_label')}: ${t('ocorrencias:envolvido.sem_documento')}`}
              </span>
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

      {permitirEvidencias && (
        <fieldset>
          <legend>{t('ocorrencias:evidencias.titulo')}</legend>
          <label>
            {t('ocorrencias:evidencias.selecionar')}
            <input
              type="file"
              accept=".pdf,.jpg,.jpeg,.png,application/pdf,image/jpeg,image/png"
              multiple
              onChange={(e) => set('evidencias', [...v.evidencias, ...Array.from(e.target.files ?? [])])}
            />
          </label>
          <small className="muted">{t('ocorrencias:evidencias.ajuda')}</small>
          <ul className="lista">
            {v.evidencias.map((arquivo, idx) => (
              <li key={`${arquivo.name}-${idx}`}>
                <span>{arquivo.name} · {(arquivo.size / 1024).toFixed(1)} KB</span>
                <button type="button" className="btn btn-link" onClick={() => set('evidencias', v.evidencias.filter((_, i) => i !== idx))}>{t('common:actions.remover')}</button>
              </li>
            ))}
          </ul>
        </fieldset>
      )}

      <p className="muted small"><span className="obrigatorio">*</span> {t('ocorrencias:form.obrigatorio')}</p>
      <button type="submit" className="btn btn-primary" disabled={ocupado}>
        {ocupado ? t('common:actions.loading') : rotuloEnviar}
      </button>
    </form>
  );
};
