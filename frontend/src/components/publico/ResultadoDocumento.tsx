import React from 'react';
import { useTranslation } from 'react-i18next';
import { StatusBadge } from '../StatusBadge';
import type { DocumentoAutenticado } from '../../types/api';

interface Props {
  dados: DocumentoAutenticado;
}

/** Espelho de conferência do documento emitido (RF08 / UC08 passo 5): selo de situação, dados de emissão e hash. */
export const ResultadoDocumento: React.FC<Props> = ({ dados }) => {
  const { t, i18n } = useTranslation(['publico', 'ocorrencias']);
  const localeData = i18n.language && i18n.language.startsWith('en') ? 'en-US' : 'pt-BR';
  const fmt = (iso: string) => new Date(iso).toLocaleString(localeData);
  const valido = dados.situacao === 'VALIDO';

  const envolvidos = Object.entries(dados.envolvidos_por_tipo)
    .map(([tipo, qtd]) => `${qtd} × ${t(`ocorrencias:envolvido.${tipo}`)}`)
    .join(' · ');

  return (
    <div className="resultado-publico resultado-autenticacao" data-situacao={dados.situacao}>
      <div className={`alerta ${valido ? 'sucesso' : 'erro'}`} role="status">
        <strong>{valido ? '✔ ' : '⚠ '}{t(`publico:resultado.${dados.situacao}`)}</strong>
        <div className="small">{t(`publico:resultado.explicacao_${dados.situacao}`)}</div>
      </div>

      <dl className="grid2">
        <dt>{t('publico:resultado.protocolo')}</dt><dd><strong>{dados.numero_protocolo}</strong></dd>
        <dt>{t('publico:resultado.status')}</dt><dd><StatusBadge status={dados.status_ocorrencia} /></dd>
        <dt>{t('publico:resultado.emitido_em')}</dt><dd>{fmt(dados.emitido_em)}</dd>
        <dt>{t('publico:resultado.consultado_em')}</dt><dd>{fmt(dados.consultado_em)}</dd>
        <dt>{t('publico:resultado.natureza')}</dt><dd>{dados.natureza}</dd>
        <dt>{t('publico:resultado.data_fato')}</dt><dd>{fmt(dados.data_hora_fato)}</dd>
        <dt>{t('publico:resultado.envolvidos')}</dt><dd>{envolvidos || '—'}</dd>
        <dt>{t('publico:resultado.evidencias')}</dt><dd>{dados.quantidade_evidencias}</dd>
      </dl>

      {dados.tipificacoes.length > 0 && (
        <>
          <h4>{t('publico:resultado.tipificacoes')}</h4>
          <ul className="lista">
            {dados.tipificacoes.map((tp, i) => (
              <li key={i}><span><strong>{tp.artigo}</strong> — {tp.descricao}</span></li>
            ))}
          </ul>
        </>
      )}

      <p className="muted small hash">
        {t('publico:resultado.hash')}: <code>{dados.hash_integridade}</code>
      </p>
    </div>
  );
};
