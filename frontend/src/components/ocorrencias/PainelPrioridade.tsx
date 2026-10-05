import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useToast } from '../../hooks/useToast';
import { mensagemDeErro } from '../../services/api';
import { ocorrenciasService } from '../../services/ocorrenciasService';
import { PRIORIDADES, type OcorrenciaDetalhe, type PrioridadeOcorrencia } from '../../types/api';
import { PrioridadeBadge } from '../PrioridadeBadge';

const MINIMO_JUSTIFICATIVA = 10;

interface Props {
  detalhe: OcorrenciaDetalhe;
  onAlterada: (atualizada: OcorrenciaDetalhe) => void;
}

/** Delegado ajusta a gravidade com justificativa; o ajuste fica na trilha de auditoria (sugestão #7). */
export const PainelPrioridade: React.FC<Props> = ({ detalhe, onAlterada }) => {
  const { t } = useTranslation(['ocorrencias', 'common']);
  const { avisar } = useToast();
  const [nova, setNova] = useState<PrioridadeOcorrencia | ''>('');
  const [justificativa, setJustificativa] = useState('');
  const [ocupado, setOcupado] = useState(false);
  const opcoes = PRIORIDADES.filter((p) => p !== detalhe.prioridade);

  const salvar = async () => {
    if (!nova) return;
    if (justificativa.trim().length < MINIMO_JUSTIFICATIVA) {
      avisar(t('ocorrencias:revisao.justificativa_curta'), 'erro');
      return;
    }
    setOcupado(true);
    try {
      onAlterada(await ocorrenciasService.redefinirPrioridade(detalhe.ocorrencia_id, nova, justificativa.trim()));
      setNova('');
      setJustificativa('');
      avisar(t('ocorrencias:prioridade.ok'), 'sucesso');
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    } finally {
      setOcupado(false);
    }
  };

  return (
    <div className="painel-prioridade">
      <h4>{t('ocorrencias:prioridade.titulo')} <PrioridadeBadge prioridade={detalhe.prioridade} /></h4>
      <div className="painel-prioridade-linha">
        <label>
          {t('ocorrencias:prioridade.nova')}
          <select value={nova} onChange={(e) => setNova(e.target.value as PrioridadeOcorrencia | '')}>
            <option value="">—</option>
            {opcoes.map((p) => <option key={p} value={p}>{t(`common:prioridade.${p}`)}</option>)}
          </select>
        </label>
        <label className="painel-prioridade-justificativa">
          {t('ocorrencias:prioridade.justificativa')} <span className="muted contador">({justificativa.trim().length}/{MINIMO_JUSTIFICATIVA}+)</span>
          <input maxLength={2000} value={justificativa} onChange={(e) => setJustificativa(e.target.value)} disabled={!nova} />
        </label>
      </div>
      <button className="btn btn-sm" disabled={!nova || ocupado} onClick={salvar}>{t('ocorrencias:prioridade.salvar')}</button>
    </div>
  );
};
