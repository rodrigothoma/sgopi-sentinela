import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { EnvolvidoForm } from './EnvolvidoForm';
import { SeletorCoordenada } from '../painel/SeletorCoordenada';
import { TipificacaoForm } from './TipificacaoForm';
import { ItemApreendidoForm } from './ItemApreendidoForm';
import { PRIORIDADES, type EnvolvidoDTO, type ItemApreendidoDTO, type PrioridadeOcorrencia, type RegistrarOcorrenciaRequest, type TipificacaoDTO } from '../../types/api';

export interface ValoresOcorrencia {
  natureza: string; descricao: string; localizacao: string;
  latitude: number | null; longitude: number | null; dataHoraFatoLocal: string;
  envolvidos: EnvolvidoDTO[]; tipificacoes: TipificacaoDTO[]; evidencias: File[];
  /** RF03 — apreensão concomitante ao registro (opcional). */
  itensApreendidos: ItemApreendidoDTO[];
  /** Sugestão #7 — ausente: o backend sugere pela natureza/tipificações. */
  prioridade?: PrioridadeOcorrencia;
}

export const valoresVazios = (): ValoresOcorrencia => ({
  natureza: '', descricao: '', localizacao: '', latitude: null, longitude: null,
  dataHoraFatoLocal: paraInputLocal(new Date()), envolvidos: [], tipificacoes: [], evidencias: [], itensApreendidos: [],
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
    ...(v.itensApreendidos.length > 0 ? { itens_apreendidos: v.itensApreendidos } : {}),
    ...(v.prioridade ? { prioridade: v.prioridade } : {}),
  };
}

interface Props {
  inicial: ValoresOcorrencia;
  onSubmit: (v: ValoresOcorrencia) => Promise<void>;
  rotuloEnviar: string;
  ocupado: boolean;
  permitirEvidencias?: boolean;
  /** Exibe a seção opcional de apreensões (só no registro: a correção não altera o inventário). */
  permitirApreensoes?: boolean;
  /** Ajuste opcional da gravidade (só no registro; depois, quem ajusta é o Delegado). */
  permitirPrioridade?: boolean;
}

const FORMATOS_EVIDENCIA = ['application/pdf', 'image/jpeg', 'image/png'];
const TAMANHO_MAXIMO_EVIDENCIA = 10 * 1024 * 1024;
const MAXIMO_EVIDENCIAS = 10;
const MINIMO_DESCRICAO = 20;

export const OcorrenciaForm: React.FC<Props> = ({ inicial, onSubmit, rotuloEnviar, ocupado, permitirEvidencias = false, permitirApreensoes = false, permitirPrioridade = false }) => {
  const { t } = useTranslation(['ocorrencias', 'common']);
  const [v, setV] = useState<ValoresOcorrencia>(inicial);
  const [erro, setErro] = useState<string | null>(null);
  const [erroEvidencias, setErroEvidencias] = useState<string | null>(null);
  const [comApreensao, setComApreensao] = useState(inicial.itensApreendidos.length > 0);
  const set = <K extends keyof ValoresOcorrencia>(k: K, val: ValoresOcorrencia[K]) => setV((x) => ({ ...x, [k]: val }));

  const validar = (): string | null => {
    if (!v.natureza.trim() || !v.localizacao.trim()) return t('ocorrencias:erros.campos_obrigatorios');
    if (v.descricao.trim().length < MINIMO_DESCRICAO) return t('ocorrencias:erros.descricao_curta');
    if (v.latitude === null || v.longitude === null) return t('ocorrencias:erros.sem_coordenada');
    if (new Date(v.dataHoraFatoLocal).getTime() > Date.now()) return t('ocorrencias:erros.data_futura');
    if (v.envolvidos.length === 0) return t('ocorrencias:erros.sem_envolvidos');
    if (v.evidencias.length > MAXIMO_EVIDENCIAS) return t('ocorrencias:evidencias.limite');
    if (v.evidencias.some((arquivo) => !FORMATOS_EVIDENCIA.includes(arquivo.type))) return t('ocorrencias:evidencias.formato_invalido');
    if (v.evidencias.some((arquivo) => arquivo.size > TAMANHO_MAXIMO_EVIDENCIA)) return t('ocorrencias:evidencias.tamanho_excedido');
    return null;
  };

  /** Recusa já na seleção o que o backend recusaria (formato, tamanho, limite) — o arquivo nem entra na lista. */
  const adicionarEvidencias = (entrada: HTMLInputElement) => {
    const selecionados = Array.from(entrada.files ?? []);
    entrada.value = ''; // permite selecionar de novo o mesmo arquivo após removê-lo
    const formatoInvalido = selecionados.filter((arquivo) => !FORMATOS_EVIDENCIA.includes(arquivo.type));
    const grandes = selecionados.filter((arquivo) => FORMATOS_EVIDENCIA.includes(arquivo.type) && arquivo.size > TAMANHO_MAXIMO_EVIDENCIA);
    const validos = selecionados.filter((arquivo) => !formatoInvalido.includes(arquivo) && !grandes.includes(arquivo));
    const vagas = Math.max(0, MAXIMO_EVIDENCIAS - v.evidencias.length);
    const problemas = [
      formatoInvalido.length > 0 && t('ocorrencias:evidencias.recusados_formato', { arquivos: formatoInvalido.map((a) => a.name).join(', ') }),
      grandes.length > 0 && t('ocorrencias:evidencias.recusados_tamanho', { arquivos: grandes.map((a) => a.name).join(', ') }),
      validos.length > vagas && t('ocorrencias:evidencias.limite'),
    ].filter(Boolean) as string[];
    setErroEvidencias(problemas.length > 0 ? problemas.join(' ') : null);
    if (validos.length > 0 && vagas > 0) set('evidencias', [...v.evidencias, ...validos.slice(0, vagas)]);
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
        {permitirPrioridade && (
          <label htmlFor="prioridade">
            {t('ocorrencias:prioridade.campo')} <span className="muted">({t('ocorrencias:prioridade.ajuda')})</span>
            <select id="prioridade" value={v.prioridade ?? ''} onChange={(e) => set('prioridade', (e.target.value || undefined) as PrioridadeOcorrencia | undefined)}>
              <option value="">{t('ocorrencias:prioridade.automatica')}</option>
              {PRIORIDADES.map((p) => <option key={p} value={p}>{t(`common:prioridade.${p}`)}</option>)}
            </select>
          </label>
        )}
      </section>

      <section className="secao">
        <label htmlFor="localizacao">
          {t('ocorrencias:form.localizacao_label')} <span className="obrigatorio">*</span>
          <input
            id="localizacao"
            maxLength={150}
            value={v.localizacao}
            onChange={(e) => set('localizacao', e.target.value)}
            placeholder={t('ocorrencias:form.localizacao_placeholder')}
          />
        </label>
        <label style={{ marginTop: 12 }}>
          {t('ocorrencias:form.coordenada_label')} <span className="muted">({t('ocorrencias:form.coordenada_ajuda')})</span>
        </label>
        <SeletorCoordenada
          latitude={v.latitude}
          longitude={v.longitude}
          onChange={(lat, lon) => setV((x) => ({ ...x, latitude: lat, longitude: lon }))}
        />
      </section>

      <section className="secao">
        <h3>{t('ocorrencias:form.secao_narrativa')}</h3>
        <label htmlFor="descricao">
          {t('ocorrencias:form.descricao_label')} <span className="obrigatorio">*</span>{' '}
          <span className={`contador ${descricaoLen < MINIMO_DESCRICAO ? 'obrigatorio' : 'muted'}`}>
            ({descricaoLen}/{MINIMO_DESCRICAO}+ · {t('ocorrencias:form.descricao_ajuda')})
          </span>
          <textarea id="descricao" rows={6} maxLength={500} value={v.descricao} onChange={(e) => set('descricao', e.target.value)} placeholder={t('ocorrencias:form.descricao_placeholder')} />
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
              onChange={(e) => adicionarEvidencias(e.target)}
            />
          </label>
          <small className="muted">{t('ocorrencias:evidencias.ajuda')}</small>
          {erroEvidencias && <div className="alerta erro" role="alert" data-cy="erro-evidencias">{erroEvidencias}</div>}
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

      {permitirApreensoes && (
        <fieldset className="apreensoes-registro" data-cy="secao-apreensoes">
          <legend>
            <label className="apreensoes-toggle">
              <input type="checkbox" checked={comApreensao} onChange={(e) => setComApreensao(e.target.checked)} data-cy="toggle-apreensoes" />
              {' '}{t('ocorrencias:apreensoes.secao_registro')} <span className="muted">({t('ocorrencias:apreensoes.opcional')})</span>
            </label>
          </legend>
          {comApreensao && (
            <>
              <p className="muted small">{t('ocorrencias:apreensoes.ajuda_registro')}</p>
              <ItemApreendidoForm
                onAdd={(item) => set('itensApreendidos', [...v.itensApreendidos, item])}
                lacresEmUso={v.itensApreendidos.map((i) => i.numero_lacre)}
              />
              <ul className="lista">
                {v.itensApreendidos.map((item, idx) => (
                  <li key={item.numero_lacre}>
                    <span>
                      <strong>{item.numero_lacre}</strong> · {t(`ocorrencias:apreensoes.tipo.${item.tipo}`)} · {item.quantidade} {t(`ocorrencias:apreensoes.unidade.${item.unidade}`)} · {item.descricao}
                      <br /><small className="muted">{t(`ocorrencias:apreensoes.estado.${item.estado_conservacao}`)} · {item.localizacao_deposito}</small>
                    </span>
                    <button type="button" className="btn btn-link" onClick={() => set('itensApreendidos', v.itensApreendidos.filter((_, i) => i !== idx))}>{t('common:actions.remover')}</button>
                  </li>
                ))}
              </ul>
            </>
          )}
        </fieldset>
      )}

      <p className="muted small"><span className="obrigatorio">*</span> {t('ocorrencias:form.obrigatorio')}</p>
      <button type="submit" className="btn btn-primary" disabled={ocupado}>
        {ocupado ? t('common:actions.loading') : rotuloEnviar}
      </button>
    </form>
  );
};
