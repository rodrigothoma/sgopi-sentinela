import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

import ptCommon from './locales/pt/common.json';
import ptAuth from './locales/pt/auth.json';
import ptOcorrencias from './locales/pt/ocorrencias.json';
import ptPainel from './locales/pt/painel.json';
import ptPublico from './locales/pt/publico.json';
import ptInicio from './locales/pt/inicio.json';

import enCommon from './locales/en/common.json';
import enAuth from './locales/en/auth.json';
import enOcorrencias from './locales/en/ocorrencias.json';
import enPainel from './locales/en/painel.json';
import enPublico from './locales/en/publico.json';
import enInicio from './locales/en/inicio.json';

export const IDIOMAS_SUPORTADOS = ['pt', 'en'] as const;
export type Idioma = (typeof IDIOMAS_SUPORTADOS)[number];

const CHAVE_IDIOMA = 'sgopi.idioma';

export const resources = {
  pt: {
    common: ptCommon,
    auth: ptAuth,
    ocorrencias: ptOcorrencias,
    painel: ptPainel,
    publico: ptPublico,
    inicio: ptInicio,
  },
  en: {
    common: enCommon,
    auth: enAuth,
    ocorrencias: enOcorrencias,
    painel: enPainel,
    publico: enPublico,
    inicio: enInicio,
  },
} as const;

const ehIdiomaSuportado = (valor: string | null): valor is Idioma =>
  (IDIOMAS_SUPORTADOS as readonly string[]).includes(valor ?? '');

let idiomaInicial: Idioma = 'pt';
try {
  const salvo = localStorage.getItem(CHAVE_IDIOMA);
  if (ehIdiomaSuportado(salvo)) {
    idiomaInicial = salvo;
  }
} catch {
  /* sem localStorage */
}

i18n.use(initReactI18next).init({
  resources,
  lng: idiomaInicial,
  fallbackLng: 'pt',
  ns: Object.keys(resources.pt),
  defaultNS: 'common',
  interpolation: { escapeValue: false },
});

/** Troca o idioma da aplicação e persiste a escolha para as próximas sessões. */
export const trocarIdiomaGlobal = (lng: string): void => {
  const normalizado = lng.slice(0, 2);
  const idioma: Idioma = ehIdiomaSuportado(normalizado) ? normalizado : 'pt';
  void i18n.changeLanguage(idioma);
  try {
    localStorage.setItem(CHAVE_IDIOMA, idioma);
  } catch {
    /* sem localStorage */
  }
};

export default i18n;
