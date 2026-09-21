/// <reference types="cypress" />

/**
 * Issue #47 — Testes E2E: Painel de Trilha de Auditoria Imutável (RNF02 / RNF03).
 * Pré-requisito: backend (:8000) e frontend (:3000) rodando com seed de dados.
 */

describe('Issue #47 — Trilha de Auditoria Imutável e RBAC (RNF02 / RNF03)', () => {
  it('delegado acessa a trilha de auditoria, visualiza KPIs e inspeciona logs', () => {
    // 1. Gera uma ação no sistema para garantir registros na trilha
    cy.criarOcorrenciaApi().then(() => {
      // 2. Login como Delegado e navegação para /auditoria
      cy.login('delegado', '/auditoria');

      // 3. Valida elementos chave da tela
      cy.contains('h1', 'Trilha de Auditoria').should('be.visible');

      // 4. Valida KPIs
      cy.get('.kpi-card').should('have.length', 3);
      cy.get('.kpi-card').first().find('.kpi-val').should('not.be.empty');

      // 5. Tabela de logs possui registros
      cy.get('table.tabela tbody tr').should('have.length.at.least', 1);

      // 6. Teste de busca textual
      cy.get('input[placeholder*="Filtrar"]').type('Ocorrencia');
      cy.get('table.tabela tbody tr').should('have.length.at.least', 1);

      // 7. Inspeção do payload
      cy.contains('button', 'Inspecionar').first().click();
      cy.contains('div[role="dialog"]', 'Inspeção de Auditoria').should('be.visible');
      cy.contains('div[role="dialog"]', 'Visão Operacional').should('be.visible');
      cy.contains('button', 'JSON Técnico').click();
      cy.contains('div[role="dialog"]', 'Novo Estado').should('be.visible');

      // 8. Fecha o modal
      cy.contains('div[role="dialog"] button', 'Fechar').click();
      cy.get('div[role="dialog"]').should('not.exist');
    });
  });

  it('agente não vê o link de auditoria no menu e não acessa a rota /auditoria', () => {
    cy.login('agente', '/minhas');
    // Não deve existir link para auditoria no menu
    cy.get('nav a[href="/auditoria"]').should('not.exist');

    // Ao tentar acessar diretamente a URL /auditoria, é impedido
    cy.visit('/auditoria');
    cy.url().should('not.include', '/auditoria');
  });
});
