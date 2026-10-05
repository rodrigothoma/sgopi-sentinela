import { defineConfig, loadEnv, type Plugin } from 'vite';
import react from '@vitejs/plugin-react';

/**
 * Content-Security-Policy do bundle de produção (defesa em profundidade contra XSS). Só entra no
 * build: em `vite dev` o preâmbulo do React Refresh é um script inline e quebraria com `script-src 'self'`.
 */
const montarCsp = (apiBaseUrl: string): string => {
  // API servida em outra origem (VITE_API_BASE_URL): REST e WebSocket precisam estar no connect-src
  const api = apiBaseUrl ? new URL(apiBaseUrl) : null;
  const origensApi = api ? ` ${api.origin} ${api.origin.replace(/^http/, 'ws')}` : '';
  return [
    "default-src 'self'",
    "script-src 'self'",
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
    "font-src 'self' https://fonts.gstatic.com",
    "img-src 'self' data: blob: https://*.tile.openstreetmap.org",
    `connect-src 'self' ws: wss:${origensApi}`,
    "object-src 'none'",
    "base-uri 'self'",
  ].join('; ');
};

const cspEmProducao = (csp: string): Plugin => ({
  name: 'sgopi-csp',
  apply: 'build',
  transformIndexHtml: () => [
    { tag: 'meta', attrs: { 'http-equiv': 'Content-Security-Policy', content: csp }, injectTo: 'head-prepend' },
  ],
});

export default defineConfig(({ mode }) => ({
  plugins: [react(), cspEmProducao(montarCsp(loadEnv(mode, process.cwd(), 'VITE_').VITE_API_BASE_URL ?? ''))],
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          leaflet: ['leaflet', 'leaflet.heat'],
          react: ['react', 'react-dom', 'react-router-dom'],
          i18n: ['i18next', 'react-i18next'],
        },
      },
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/v1': { target: 'http://localhost:8000', changeOrigin: true, ws: true },
      '/health': { target: 'http://localhost:8000', changeOrigin: true },
    },
  },
}));
