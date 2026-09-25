import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  ESTADOS_CONSERVACAO, TIPOS_ITEM_APREENDIDO, UNIDADES_MEDIDA,
  type EstadoConservacao, type ItemApreendidoDTO, type TipoItemApreendido, type UnidadeMedida,
} from '../../types/api';

interface Props {
  onAdd: (item: ItemApreendidoDTO) => void | Promise<void>;
  /** Lacres já usados (na ocorrência ou no formulário) — bloqueia duplicidade antes de chamar a API. */
  lacresEmUso?: readonly string[];
  ocupado?: boolean;
  rotuloAdicionar?: string;
}

type ProblemaItem = 'descricao_vazia' | 'quantidade_invalida' | 'lacre_vazio' | 'lacre_duplicado' | 'localizacao_vazia' | 'arma_sem_calibre_ou_marca';

const vazio = (): ItemApreendidoDTO => ({
  tipo: 'OBJETO', descricao: '', quantidade: 1, unidade: 'UNIDADE', estado_conservacao: 'BOM',
  numero_lacre: '', localizacao_deposito: '', numero_serie: '', marca: '', calibre: '',
});

const opcional = (s?: string | null) => (s && s.trim() ? s.trim() : null);

/** Espelha as regras do domínio (ItemApreendido.__post_init__) para feedback imediato na borda. */
export function validarItemApreendido(v: ItemApreendidoDTO, lacresEmUso: readonly string[] = []): ProblemaItem | null {
  if (!v.descricao.trim()) return 'descricao_vazia';
  if (!Number.isInteger(v.quantidade) || v.quantidade <= 0) return 'quantidade_invalida';
  if (!v.numero_lacre.trim()) return 'lacre_vazio';
  if (lacresEmUso.includes(v.numero_lacre.trim().toUpperCase())) return 'lacre_duplicado';
  if (!v.localizacao_deposito.trim()) return 'localizacao_vazia';
  if (v.tipo === 'ARMA_DE_FOGO' && (!opcional(v.marca) || !opcional(v.calibre))) return 'arma_sem_calibre_ou_marca';
  return null;
}

export function normalizarItemApreendido(v: ItemApreendidoDTO): ItemApreendidoDTO {
  return {
    tipo: v.tipo, descricao: v.descricao.trim(), quantidade: v.quantidade, unidade: v.unidade,
    estado_conservacao: v.estado_conservacao, numero_lacre: v.numero_lacre.trim().toUpperCase(),
    localizacao_deposito: v.localizacao_deposito.trim(),
    numero_serie: opcional(v.numero_serie), marca: opcional(v.marca), calibre: opcional(v.calibre),
  };
}

/** Subformulário de item apreendido (RF03): usado no registro concomitante e na aba de apreensões. */
export const ItemApreendidoForm: React.FC<Props> = ({ onAdd, lacresEmUso = [], ocupado = false, rotuloAdicionar }) => {
  const { t } = useTranslation('ocorrencias');
  const [v, setV] = useState<ItemApreendidoDTO>(vazio());
  const [erro, setErro] = useState<ProblemaItem | null>(null);
  const set = <K extends keyof ItemApreendidoDTO>(k: K, val: ItemApreendidoDTO[K]) => { setV((x) => ({ ...x, [k]: val })); setErro(null); };
  const armaDeFogo = v.tipo === 'ARMA_DE_FOGO';

  const adicionar = async () => {
    const problema = validarItemApreendido(v, lacresEmUso);
    if (problema) { setErro(problema); return; }
    try {
      await onAdd(normalizarItemApreendido(v));
      setV(vazio());
    } catch {
      /* o chamador já exibiu o erro; os valores ficam para correção */
    }
  };

  const aoEnter = (e: React.KeyboardEvent) => { if (e.key === 'Enter') { e.preventDefault(); void adicionar(); } };

  return (
    <div className="subform apreensao-form" data-cy="item-apreendido-form">
      <div className="grid-apreensao">
        <div>
          <label htmlFor="apreensao-tipo">{t('apreensoes.tipo_label')} <span className="obrigatorio">*</span></label>
          <select id="apreensao-tipo" value={v.tipo} onChange={(e) => set('tipo', e.target.value as TipoItemApreendido)}>
            {TIPOS_ITEM_APREENDIDO.map((tp) => <option key={tp} value={tp}>{t(`apreensoes.tipo.${tp}`)}</option>)}
          </select>
        </div>
        <div className="col-2">
          <label htmlFor="apreensao-descricao">{t('apreensoes.descricao_label')} <span className="obrigatorio">*</span></label>
          <input id="apreensao-descricao" value={v.descricao} maxLength={2000} placeholder={t('apreensoes.descricao_placeholder')} onChange={(e) => set('descricao', e.target.value)} onKeyDown={aoEnter} />
        </div>
        <div>
          <label htmlFor="apreensao-quantidade">{t('apreensoes.quantidade_label')} <span className="obrigatorio">*</span></label>
          <input id="apreensao-quantidade" type="number" min={1} step={1} value={v.quantidade} onChange={(e) => set('quantidade', Number(e.target.value))} onKeyDown={aoEnter} />
        </div>
        <div>
          <label htmlFor="apreensao-unidade">{t('apreensoes.unidade_label')}</label>
          <select id="apreensao-unidade" value={v.unidade} onChange={(e) => set('unidade', e.target.value as UnidadeMedida)}>
            {UNIDADES_MEDIDA.map((u) => <option key={u} value={u}>{t(`apreensoes.unidade.${u}`)}</option>)}
          </select>
        </div>
        <div>
          <label htmlFor="apreensao-estado">{t('apreensoes.estado_label')} <span className="obrigatorio">*</span></label>
          <select id="apreensao-estado" value={v.estado_conservacao} onChange={(e) => set('estado_conservacao', e.target.value as EstadoConservacao)}>
            {ESTADOS_CONSERVACAO.map((ec) => <option key={ec} value={ec}>{t(`apreensoes.estado.${ec}`)}</option>)}
          </select>
        </div>
        <div>
          <label htmlFor="apreensao-lacre">{t('apreensoes.lacre_label')} <span className="obrigatorio">*</span></label>
          <input id="apreensao-lacre" value={v.numero_lacre} maxLength={60} placeholder={t('apreensoes.lacre_placeholder')} onChange={(e) => set('numero_lacre', e.target.value.toUpperCase())} onKeyDown={aoEnter} />
        </div>
        <div>
          <label htmlFor="apreensao-serie">{t('apreensoes.serie_label')}</label>
          <input id="apreensao-serie" value={v.numero_serie ?? ''} maxLength={100} placeholder={t('apreensoes.serie_placeholder')} onChange={(e) => set('numero_serie', e.target.value)} onKeyDown={aoEnter} />
        </div>
        <div>
          <label htmlFor="apreensao-marca">{t('apreensoes.marca_label')} {armaDeFogo && <span className="obrigatorio">*</span>}</label>
          <input id="apreensao-marca" value={v.marca ?? ''} maxLength={100} onChange={(e) => set('marca', e.target.value)} onKeyDown={aoEnter} />
        </div>
        <div>
          <label htmlFor="apreensao-calibre">{t('apreensoes.calibre_label')} {armaDeFogo && <span className="obrigatorio">*</span>}</label>
          <input id="apreensao-calibre" value={v.calibre ?? ''} maxLength={50} placeholder={t('apreensoes.calibre_placeholder')} onChange={(e) => set('calibre', e.target.value)} onKeyDown={aoEnter} />
        </div>
        <div className="col-2">
          <label htmlFor="apreensao-localizacao">{t('apreensoes.localizacao_label')} <span className="obrigatorio">*</span></label>
          <input id="apreensao-localizacao" value={v.localizacao_deposito} maxLength={255} placeholder={t('apreensoes.localizacao_placeholder')} onChange={(e) => set('localizacao_deposito', e.target.value)} onKeyDown={aoEnter} />
        </div>
      </div>
      {erro ? <p className="campo-erro" role="alert">{t(`apreensoes.erro_${erro}`)}</p> : <p className="muted small" style={{ margin: '6px 0 0' }}>{t(armaDeFogo ? 'apreensoes.ajuda_arma' : 'apreensoes.ajuda')}</p>}
      <div className="acoes" style={{ marginTop: 10 }}>
        <button type="button" className="btn btn-primary" disabled={ocupado} onClick={() => void adicionar()}>
          {rotuloAdicionar ?? t('apreensoes.adicionar')}
        </button>
      </div>
    </div>
  );
};
