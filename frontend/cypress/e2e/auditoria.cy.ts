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

      // 6. Paginação no servidor visível abaixo da tabela
      cy.get('[data-cy="paginacao"]').should('contain.text', 'Exibindo').and('contain.text', 'Página 1');

      // 7. Teste de busca textual (vale para a página atual)
      cy.get('[data-cy="auditoria-busca"]').type('Ocorrencia');
      cy.get('table.tabela tbody tr').should('have.length.at.least', 1);
      cy.get('[data-cy="auditoria-busca"]').clear();

      // 8. Inspeção do payload
      cy.contains('button', 'Inspecionar').first().click();
      cy.contains('div[role="dialog"]', 'Inspeção de Auditoria').should('be.visible');
      cy.contains('div[role="dialog"]', 'Visão Operacional').should('be.visible');
      cy.contains('button', 'JSON Técnico').click();
      cy.contains('div[role="dialog"]', 'Novo Estado').should('be.visible');

      // 9. Fecha o modal
      cy.contains('div[role="dialog"] button', 'Fechar').click();
      cy.get('div[role="dialog"]').should('not.exist');

      // 10. Período sem registros esvazia a trilha; limpar o período volta a listar
      cy.get('[data-cy="auditoria-data-de"]').type('2020-01-01');
      cy.get('[data-cy="auditoria-data-ate"]').type('2020-01-31');
      cy.contains('table.tabela tbody', 'Nenhum registro de auditoria encontrado').should('be.visible');
      cy.contains('button', 'Limpar período').click();
      cy.get('table.tabela tbody tr').should('have.length.at.least', 1);
    });
  });

  it('agente não vê o link de auditoria no menu e não acessa a rota /auditoria', () => {
    cy.login('agente', '/minhas');
    // Não deve existir link para auditoria no menu
    cy.get('nav a[href="/auditoria"]').should('not.exist');

    // Ao tentar acessar diretamente a URL /auditoria, vê o aviso de acesso negado (sem a trilha)
    cy.visit('/auditoria');
    cy.get('[data-cy="acesso-negado"]').should('contain.text', 'Acesso não autorizado');
    cy.contains('Trilha de Auditoria').should('not.exist');
  });
});
