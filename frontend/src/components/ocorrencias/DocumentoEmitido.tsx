import React from 'react';
import { useTranslation } from 'react-i18next';
import { QRCodeSVG } from 'qrcode.react';
import { documentosService } from '../../services/documentosService';

/** RF08: chave pública e QR Code do documento emitido na validação (UC08 pré-condição). */
export const DocumentoEmitido: React.FC<{ chave: string }> = ({ chave }) => {
  const { t } = useTranslation('ocorrencias');
  const url = documentosService.urlPublica(chave);
  return (
    <div className="callout documento-emitido">
      <div>
        <strong>{t('detalhe.documento_emitido')}</strong>
        <div className="chave-autenticidade"><code>{chave}</code></div>
        <a href={url} target="_blank" rel="noreferrer" className="small">{t('detalhe.abrir_portal')}</a>
      </div>
      <QRCodeSVG value={url} size={96} bgColor="transparent" fgColor="#f8fafc" aria-label={t('detalhe.qr_alt')} />
    </div>
  );
};
