/**
 * Regressão do XSS armazenado (crítico #1 da análise técnica): a natureza é texto livre e o Leaflet
 * interpreta strings de tooltip/popup como HTML. O payload precisa aparecer como texto, nunca executar.
 */
const PAYLOAD = '<img src=x onerror="window.__xss=1">';

describe('Painel Tático — natureza com markup não executa', () => {
  it('tooltip do marcador mostra o payload como texto', () => {
    cy.criarOcorrenciaApi({ natureza: PAYLOAD }).then((o) => {
      cy.apiComo('delegado', 'POST', `/v1/ocorrencias/${o.ocorrencia_id}/validar`, {}).its('status').should('eq', 200);
      cy.login('operador', '/painel');
      cy.get('.leaflet-marker-icon').should('have.length.greaterThan', 0).each(($m) => {
        cy.wrap($m).trigger('mouseover', { force: true });
      });
      cy.get('.leaflet-tooltip').should('contain.text', PAYLOAD);
      cy.get('.leaflet-tooltip img[src="x"]').should('not.exist');
      cy.window().its('__xss').should('be.undefined');
    });
  });
});
