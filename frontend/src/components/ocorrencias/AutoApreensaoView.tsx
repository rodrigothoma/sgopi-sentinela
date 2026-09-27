import React from 'react';
import { createPortal } from 'react-dom';
import { useTranslation } from 'react-i18next';
import type { AutoApreensao } from '../../types/api';
import { formatarNatureza } from '../../utils/formatarNatureza';

const fmt = (iso: string) => new Date(iso).toLocaleString();

interface Props {
  auto: AutoApreensao;
  onFechar: () => void;
}

/**
 * Auto de Apreensão em formato imprimível (RF03). Renderizado em portal para que a
 * regra @media print isole só o documento; a emissão já foi auditada pelo backend.
 */
export const AutoApreensaoView: React.FC<Props> = ({ auto, onFechar }) => {
  const { t } = useTranslation(['ocorrencias', 'common']);

  return createPortal(
    <div className="auto-overlay" role="dialog" aria-modal="true" aria-labelledby="auto-titulo">
      <div className="auto-janela">
        <div className="acoes nao-imprimir" style={{ marginTop: 0 }}>
          <button className="btn btn-primary" onClick={() => window.print()}>{t('ocorrencias:apreensoes.auto.imprimir')}</button>
          <button className="btn btn-ghost" onClick={onFechar}>{t('common:actions.cancel')}</button>
        </div>
        <article className="auto-apreensao" data-cy="auto-apreensao">
          <header className="auto-cabecalho">
            <div>
              <div className="auto-orgao">{t('ocorrencias:apreensoes.auto.orgao')}</div>
              <h1 id="auto-titulo">{t('ocorrencias:apreensoes.auto.titulo')}</h1>
            </div>
            <div className="auto-numero">
              <div className="muted small">{t('ocorrencias:apreensoes.auto.numero')}</div>
              <strong>{auto.numero}</strong>
            </div>
          </header>

          <dl className="grid2 auto-dados">
            <dt>{t('ocorrencias:apreensoes.auto.protocolo')}</dt><dd>{auto.numero_protocolo}</dd>
            <dt>{t('ocorrencias:form.natureza_label')}</dt><dd>{formatarNatureza(auto.natureza, t)}</dd>
            <dt>{t('ocorrencias:form.data_hora_fato_label')}</dt><dd>{fmt(auto.data_hora_fato)}</dd>
            <dt>{t('ocorrencias:form.localizacao_label')}</dt><dd>{auto.localizacao}</dd>
            <dt>{t('ocorrencias:apreensoes.auto.agente')}</dt><dd><code>{auto.agente_policial_id}</code></dd>
            <dt>{t('ocorrencias:apreensoes.auto.emitido_em')}</dt><dd>{fmt(auto.emitido_em)}</dd>
            <dt>{t('ocorrencias:apreensoes.auto.emitido_por')}</dt><dd><code>{auto.emitido_por_id}</code></dd>
          </dl>

          <h2>{t('ocorrencias:apreensoes.auto.itens', { total: auto.itens.length })}</h2>
          <table className="tabela auto-tabela">
            <thead>
              <tr>
                <th>#</th>
                <th>{t('ocorrencias:apreensoes.lacre_label')}</th>
                <th>{t('ocorrencias:apreensoes.tipo_label')}</th>
                <th>{t('ocorrencias:apreensoes.descricao_label')}</th>
                <th>{t('ocorrencias:apreensoes.quantidade_label')}</th>
                <th>{t('ocorrencias:apreensoes.estado_label')}</th>
                <th>{t('ocorrencias:apreensoes.identificacao')}</th>
                <th>{t('ocorrencias:apreensoes.localizacao_atual')}</th>
              </tr>
            </thead>
            <tbody>
              {auto.itens.map((i, idx) => (
                <tr key={i.id}>
                  <td>{idx + 1}</td>
                  <td><strong>{i.numero_lacre}</strong></td>
                  <td>{t(`ocorrencias:apreensoes.tipo.${i.tipo}`)}</td>
                  <td>{i.descricao}</td>
                  <td>{i.quantidade} {t(`ocorrencias:apreensoes.unidade.${i.unidade}`)}</td>
                  <td>{t(`ocorrencias:apreensoes.estado.${i.estado_conservacao}`)}</td>
                  <td>
                    {[i.marca, i.calibre, i.numero_serie ? `S/N ${i.numero_serie}` : null].filter(Boolean).join(' · ') || '—'}
                  </td>
                  <td>{i.localizacao_atual}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <h2>{t('ocorrencias:apreensoes.custodia')}</h2>
          {auto.itens.map((i) => (
            <section key={i.id} className="auto-custodia">
              <h3>{i.numero_lacre} — {i.descricao}</h3>
              <ol className="historico">
                {i.movimentacoes.map((m, k) => (
                  <li key={k}>
                    <span className="muted">{fmt(m.em)}</span> · {m.origem ? <>{m.origem} → </> : null}<strong>{m.destino}</strong>
                    {' '}· <code>{m.por_id.slice(0, 8)}</code>
                    {m.observacao && <em> — {m.observacao}</em>}
                  </li>
                ))}
              </ol>
            </section>
          ))}

          <footer className="auto-rodape">
            <p className="small"><strong>SHA-256:</strong> <code>{auto.hash_sha256}</code></p>
            <p className="muted small">{t('ocorrencias:apreensoes.auto.integridade')}</p>
            <div className="auto-assinaturas">
              <div><span /> {t('ocorrencias:apreensoes.auto.assinatura_agente')}</div>
              <div><span /> {t('ocorrencias:apreensoes.auto.assinatura_delegado')}</div>
            </div>
          </footer>
        </article>
      </div>
    </div>,
    document.body,
  );
};
