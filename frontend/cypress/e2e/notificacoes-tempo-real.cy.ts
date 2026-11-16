/// <reference types="cypress" />

/**
 * Issue #68 — Notificações em tempo real: o registro de uma ocorrência (policial
 * ou pública) aparece na fila do Delegado e no sino SEM reload da página.
 * Pré-requisito: backend (:8000) e frontend (:3000) rodando com o seed.
 */

const AGORA = new Date(Date.now() - 60 * 60 * 1000).toISOString();

function registrarPublicamente() {
  return cy
    .request('POST', 'http://localhost:8000/v1/ocorrencias/publico', {
      nome_solicitante: 'Cidadã Teste',
      natureza: 'Furto',
      descricao: 'Furto de bicicleta na calçada em frente ao mercado municipal.',
      localizacao: 'Centro, Alegrete',
      latitude: -29.78,
      longitude: -55.79,
      data_hora_fato: AGORA,
      documento: '123.456.789-09',
      email: 'cidada@example.com',
      telefone: '(55) 99999-0000',
      declaracao_maioridade: true,
    })
    .its('body');
}

describe('Issue #68 — Notificações em tempo real (sino + fila reativa)', () => {
  it('ocorrência registrada entra na fila do Delegado sem reload, com badge NOVA', () => {
    cy.login('delegado', '/fila');
    // a fila montou sem a ocorrência que ainda vai ser registrada
    cy.contains('.cabecalho-lista h2', 'Fila de revisão').should('be.visible');

    registrarPublicamente().then((o) => {
      // WS empurra a ocorrência: sem F5 ela aparece na aba de triagem com o badge
      cy.contains('.lista.clicavel li', o.numero_protocolo, { timeout: 15000 }).should('be.visible');
      cy.contains('.lista.clicavel li', o.numero_protocolo).find('.badge-nova').should('be.visible');

      // abrir o detalhe consuma o badge
      cy.contains('.lista.clicavel li', o.numero_protocolo).click();
      cy.get('.detalhe').should('contain.text', o.numero_protocolo);
      cy.contains('.lista.clicavel li', o.numero_protocolo).find('.badge-nova').should('not.exist');
    });
  });

  it('sino do Delegado recebe a notificação NOVA_OCORRENCIA e leva à fila', () => {
    cy.login('delegado', '/');
    // zera pendências de runs anteriores antes de afirmar o estado inicial do sino
    cy.apiComo('delegado', 'POST', '/v1/notificacoes/marcar-todas-lidas').its('status').should('eq', 200);
    cy.get('.notification-badge').should('not.exist');

    registrarPublicamente().then((o) => {
      cy.get('.notification-badge', { timeout: 15000 }).should('be.visible');
      cy.get('.notification-bell-btn').click();
      cy.get('.notification-dropdown').should('contain.text', o.numero_protocolo);
      // o clique navega pelo link da notificação (/fila?ocorrencia=<id>)
      cy.contains('.notification-item', o.numero_protocolo).click();
      cy.url().should('include', '/fila');
      cy.get('.detalhe').should('contain.text', o.numero_protocolo);
    });
  });

  it('toast de nova ocorrência sobe na casca para o Delegado', () => {
    cy.login('delegado', '/');
    registrarPublicamente().then((o) => {
      cy.contains('.toasts .toast', o.numero_protocolo, { timeout: 15000 }).should('be.visible');
    });
  });

  it('toast de validação sobe somente para o agente autor da ocorrência', () => {
    cy.criarOcorrenciaApi().then((o) => {
      // operador não é autor de ocorrência policial: nenhuma validação o notifica
      cy.login('operador', '/');
      cy.apiComo('delegado', 'POST', `/v1/ocorrencias/${o.ocorrencia_id}/validar`).its('status').should('eq', 200);
      // eslint-disable-next-line cypress/no-unnecessary-waiting
      cy.wait(3000);
      cy.get('.toasts').should('not.contain.text', 'validada pelo Delegado');

      // uma segunda ocorrência valida com o agente autor logado: o toast sobe
      cy.criarOcorrenciaApi().then((o2) => {
        cy.login('agente', '/minhas');
        cy.apiComo('delegado', 'POST', `/v1/ocorrencias/${o2.ocorrencia_id}/validar`).its('status').should('eq', 200);
        cy.contains('.toasts .toast', 'validada pelo Delegado', { timeout: 15000 }).should('be.visible');
      });
    });
  });
});
