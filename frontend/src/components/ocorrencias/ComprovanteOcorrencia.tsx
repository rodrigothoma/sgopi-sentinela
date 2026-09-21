import React from 'react';
import { createPortal } from 'react-dom';
import { QRCodeSVG } from 'qrcode.react';
import { useTranslation } from 'react-i18next';
import type { OcorrenciaDetalhe } from '../../types/api';
import { formatarChave, urlAutenticacao } from '../../utils/autenticidade';
import { formatarNatureza } from '../../utils/formatarNatureza';

const fmt = (iso: string) => new Date(iso).toLocaleString();

interface Props {
  o: OcorrenciaDetalhe;
  /** Chave pública emitida na validação — o comprovante só existe quando ela está presente. */
  chave: string;
  onFechar: () => void;
}

/**
 * Comprovante de Ocorrência imprimível (RF08 / UC08) com QR Code de autenticidade.
 * Renderizado em portal para que a regra @media print isole só o documento. O QR
 * aponta para a página pública /autenticar/<chave>; a chave e o hash SHA-256 também
 * vão impressos para conferência manual.
 */
export const ComprovanteOcorrencia: React.FC<Props> = ({ o, chave, onFechar }) => {
  const { t } = useTranslation(['ocorrencias', 'common']);
  const url = urlAutenticacao(chave);
  const emissao = o.historico_status.find((h) => h.para === 'VALIDADA');

  return createPortal(
    <div className="auto-overlay" role="dialog" aria-modal="true" aria-labelledby="comprovante-titulo">
      <div className="auto-janela">
        <div className="acoes nao-imprimir" style={{ marginTop: 0 }}>
          <button className="btn btn-primary" onClick={() => window.print()}>{t('ocorrencias:comprovante.imprimir')}</button>
          <button className="btn btn-ghost" onClick={onFechar}>{t('common:actions.cancel')}</button>
        </div>
        <article className="auto-apreensao comprovante" data-cy="comprovante-ocorrencia">
          <header className="auto-cabecalho">
            <div>
              <div className="auto-orgao">{t('ocorrencias:comprovante.orgao')}</div>
              <h1 id="comprovante-titulo">{t('ocorrencias:comprovante.titulo')}</h1>
            </div>
            <div className="auto-numero">
              <div className="muted small">{t('ocorrencias:comprovante.protocolo')}</div>
              <strong>{o.numero_protocolo}</strong>
            </div>
          </header>

          <div className="comprovante-corpo">
            <dl className="grid2 auto-dados">
              <dt>{t('ocorrencias:form.natureza_label')}</dt><dd>{formatarNatureza(o.natureza, t)}</dd>
              <dt>{t('ocorrencias:form.data_hora_fato_label')}</dt><dd>{fmt(o.data_hora_fato)}</dd>
              <dt>{t('ocorrencias:form.localizacao_label')}</dt><dd>{o.localizacao}</dd>
              <dt>{t('ocorrencias:comprovante.status')}</dt><dd>{t(`common:status.${o.status}`, o.status)}</dd>
              <dt>{t('ocorrencias:comprovante.registrada_em')}</dt><dd>{fmt(o.criada_em)}</dd>
              {emissao && (<><dt>{t('ocorrencias:comprovante.emitido_em')}</dt><dd>{fmt(emissao.em)}</dd></>)}
              {o.validada_por_id && (<><dt>{t('ocorrencias:comprovante.validada_por')}</dt><dd><code>{o.validada_por_id}</code></dd></>)}
            </dl>

            <figure className="comprovante-qr" data-cy="comprovante-qr">
              <QRCodeSVG value={url} size={168} level="M" includeMargin />
              <figcaption className="small muted">{t('ocorrencias:comprovante.qr_legenda')}</figcaption>
            </figure>
          </div>

          {o.tipificacoes.length > 0 && (
            <>
              <h2>{t('ocorrencias:form.tipificacoes_label')}</h2>
              <ul className="lista">
                {o.tipificacoes.map((tp, i) => (<li key={i}><strong>{tp.artigo}</strong> — {tp.descricao}</li>))}
              </ul>
            </>
          )}

          <h2>{t('ocorrencias:comprovante.autenticidade')}</h2>
          <p className="small">{t('ocorrencias:comprovante.instrucao')}</p>
          <dl className="grid2 auto-dados">
            <dt>{t('ocorrencias:comprovante.chave')}</dt>
            <dd><strong className="comprovante-chave" data-cy="comprovante-chave">{formatarChave(chave)}</strong></dd>
            <dt>{t('ocorrencias:comprovante.url')}</dt>
            <dd><code>{url}</code></dd>
            <dt>{t('ocorrencias:comprovante.hash')}</dt>
            <dd><code className="comprovante-hash">{o.hash_narrativa}</code></dd>
          </dl>

          <footer className="auto-rodape">
            <p className="muted small">{t('ocorrencias:comprovante.lgpd')}</p>
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
