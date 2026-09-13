import i18n from '../../i18n';

export function toastOcorrenciaSuccess(protocolo: string): void {
  const msg = i18n.t('ocorrencias:toast.success', { protocolo });
  alert(msg);
}

export function toastOcorrenciaError(type: 'validation' | 'server' | 'not_found' = 'server'): void {
  const keyMap = {
    validation: 'ocorrencias:toast.error_validation',
    server: 'ocorrencias:toast.error_server',
    not_found: 'ocorrencias:toast.error_not_found',
  };
  alert(i18n.t(keyMap[type]));
}
