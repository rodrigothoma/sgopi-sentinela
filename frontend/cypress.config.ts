import { defineConfig } from 'cypress';

// Testes E2E (issues #21 e #22). Pré-requisito: backend (uvicorn :8000) e
// frontend (npm run dev → :3000) rodando manualmente. Ver README.
export default defineConfig({
  e2e: {
    baseUrl: 'http://localhost:3000',
    specPattern: 'cypress/e2e/**/*.cy.ts',
    supportFile: 'cypress/support/e2e.ts',
    viewportWidth: 1440,
    viewportHeight: 900,
    defaultCommandTimeout: 10000,
  },
});
