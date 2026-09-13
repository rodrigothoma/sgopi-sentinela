import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import HttpBackend from 'i18next-http-backend';

let idiomaInicial = 'pt';
try {
  idiomaInicial = localStorage.getItem('sgopi.idioma') || 'pt';
} catch {
  /* sem localStorage */
}

i18n
  .use(HttpBackend)
  .use(initReactI18next)
  .init({
    lng: idiomaInicial,
    fallbackLng: 'pt',
    ns: ['common', 'auth', 'ocorrencias', 'painel'],
    defaultNS: 'common',
    backend: { loadPath: '/locales/{{lng}}/{{ns}}.json' },
    interpolation: { escapeValue: false },
  });

export default i18n;
