import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

import ptCommon from './locales/pt/common.json';
import ptAuth from './locales/pt/auth.json';
import ptOcorrencias from './locales/pt/ocorrencias.json';
import ptPainel from './locales/pt/painel.json';
import ptPublico from './locales/pt/publico.json';

import enCommon from './locales/en/common.json';
import enAuth from './locales/en/auth.json';
import enOcorrencias from './locales/en/ocorrencias.json';
import enPainel from './locales/en/painel.json';
import enPublico from './locales/en/publico.json';

export const resources = {
  pt: {
    common: ptCommon,
    auth: ptAuth,
    ocorrencias: ptOcorrencias,
    painel: ptPainel,
    publico: ptPublico,
  },
  en: {
    common: enCommon,
    auth: enAuth,
    ocorrencias: enOcorrencias,
    painel: enPainel,
    publico: enPublico,
  },
} as const;

let idiomaInicial = 'pt';
try {
  const salvo = localStorage.getItem('sgopi.idioma');
  if (salvo === 'pt' || salvo === 'en') {
    idiomaInicial = salvo;
  }
} catch {
  /* sem localStorage */
}

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: idiomaInicial,
    fallbackLng: 'pt',
    ns: ['common', 'auth', 'ocorrencias', 'painel', 'publico'],
    defaultNS: 'common',
    interpolation: { escapeValue: false },
  });

export const trocarIdiomaGlobal = (lng: string) => {
  const normalizado = lng.slice(0, 2);
  i18n.changeLanguage(normalizado);
  try {
    localStorage.setItem('sgopi.idioma', normalizado);
  } catch {
    /* sem localStorage */
  }
};

export default i18n;
