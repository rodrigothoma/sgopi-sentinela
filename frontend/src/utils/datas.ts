import i18n from '../i18n';

/**
 * Formatação de datas no idioma ativo da aplicação (não no do navegador):
 * um navegador em inglês com o sistema em PT continua vendo 02/10/2026, 15:41.
 */
export const localeAtivo = (): string => (i18n.language?.startsWith('en') ? 'en-US' : 'pt-BR');

const paraData = (valor: string | number | Date): Date => (valor instanceof Date ? valor : new Date(valor));

export const formatarDataHora = (valor: string | number | Date, opcoes?: Intl.DateTimeFormatOptions): string =>
  paraData(valor).toLocaleString(localeAtivo(), opcoes);

export const formatarData = (valor: string | number | Date, opcoes?: Intl.DateTimeFormatOptions): string =>
  paraData(valor).toLocaleDateString(localeAtivo(), opcoes);

export const formatarHora = (valor: string | number | Date, opcoes?: Intl.DateTimeFormatOptions): string =>
  paraData(valor).toLocaleTimeString(localeAtivo(), opcoes);
