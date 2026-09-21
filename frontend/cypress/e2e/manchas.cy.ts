/// <reference types="cypress" />

/**
 * Issue #45 - Testes E2E: Manchas Criminais (heatmap) e alerta de criticidade (RF05).
 * Pré-requisito: backend (:8000) e frontend (:3000) rodando com o seed.
 */

const NATUREZA_TESTE = 'TesteMancha E2E';

function validarComoDelegado(ocorrenciaId: string) {
  cy.apiComo('delegado', 'POST', `/v1/ocorrencias/${ocorrenciaId}/validar`).its('status').should('eq', 200);
}

function semearTresOcorrenciasRecentes() {
  cy.criarOcorrenciaApi({ natureza: NATUREZA_TESTE }).then((o) => validarComoDelegado(o.ocorrencia_id));
  cy.criarOcorrenciaApi({ natureza: NATUREZA_TESTE }).then((o) => validarComoDelegado(o.ocorrencia_id));
  cy.criarOcorrenciaApi({ natureza: NATUREZA_TESTE }).then((o) => validarComoDelegado(o.ocorrencia_id));
}

function ligarManchas() {
  cy.contains('.painel-barra button', 'Manchas criminais').click();
  cy.contains('.painel-barra button', 'Ocultar manchas').should('be.visible');
}

describe('Issue #45 - Manchas criminais e criticidade', () => {
  it('liga/desliga a camada de heat sem quebrar o painel', () => {
    cy.login('operador', '/painel');
    cy.get('.painel-mapa .leaflet-container').should('be.visible');
    cy.get('.leaflet-heatmap-layer').should('not.exist');

    ligarManchas();
    cy.get('.leaflet-heatmap-layer').should('exist');

    cy.contains('.painel-barra button', 'Ocultar manchas').click();
    cy.contains('.painel-barra button', 'Manchas criminais').should('be.visible');
    cy.get('.leaflet-heatmap-layer').should('not.exist');
  });

  it('filtra por periodo e natureza mantendo o heat', () => {
    cy.login('operador', '/painel');
    ligarManchas();

    cy.contains('.painel-barra label', 'Período').find('select').select('30 dias');
    cy.get('.leaflet-heatmap-layer').should('exist');

    cy.contains('.painel-barra label', 'Período').find('select').select('7 dias');
    cy.get('.leaflet-heatmap-layer').should('exist');
  });

  it('exibe o banner de criticidade com 3+ ocorrencias em 24h', () => {
    semearTresOcorrenciasRecentes();
    cy.login('operador', '/painel');
    ligarManchas();

    cy.contains('.painel-mapa .alerta.erro', 'criticidade').should('be.visible');

    cy.contains('.painel-barra label', 'Natureza').find('select').select(NATUREZA_TESTE);
    cy.get('.leaflet-heatmap-layer').should('exist');
    cy.contains('.painel-mapa .alerta.erro', 'criticidade').should('be.visible');
  it('lista as críticas em aberto com tempo de abertura mesmo fora das 24h', () => {
    cy.criarOcorrenciaApi({ natureza: NATUREZA_TESTE }).then((o) => {
      validarComoDelegado(o.ocorrencia_id);
      cy.login('operador', '/painel');
      ligarManchas();

      cy.contains('.painel-lateral .card', 'Críticas em aberto').within(() => {
        cy.contains('li', o.numero_protocolo).should('be.visible').click();
      });
      cy.contains('.painel-lateral .card', 'Críticas em aberto').contains('li', /há \d+ (min|h|dias)/);
    });
  });
});
