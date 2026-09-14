/// <reference types="cypress" />

/**
 * Issue #21 — Testes E2E do fluxo de registro de ocorrência (RF01).
 * Pré-requisito: backend (:8000) e frontend (:3000) rodando com o seed.
 */

const PROTOCOLO = /SGOPI-\d{4}-\d{6}/;

/** Preenche o formulário mínimo válido (com coordenada nos campos numéricos). */
function preencherFormularioValido() {
  cy.contains('label', 'Natureza da ocorrência').find('input').type('Furto de veículo');
  cy.contains('label', 'Endereço').find('input').type('Av. Brasil, 500 — Alegrete/RS');
  cy.get('input[type="number"]').eq(0).type('-29.7833');
  cy.get('input[type="number"]').eq(1).type('-55.7919');
  cy.get('form.form textarea').first().type('Furto de veículo estacionado em via pública, sem violência.');
  cy.get('fieldset input[type="text"]').first().type('Maria da Silva');
  cy.contains('button', 'Adicionar envolvido').click();
}

describe('Issue #21 — Fluxo de registro', () => {
  it('bloqueia login com credenciais inválidas', () => {
    cy.loginPelaTela('agente', 'senha-errada');
    cy.get('.alerta.erro').should('be.visible');
    cy.url().should('include', '/login');
  });

  it('autentica o agente pela tela de login e vai para /registrar', () => {
    cy.loginPelaTela('agente', 'Senha@123');
    cy.url().should('include', '/registrar');
  });

  it('registra uma ocorrência e exibe o protocolo gerado', () => {
    cy.intercept('POST', '/v1/ocorrencias').as('registro');
    cy.login('agente', '/registrar');
    preencherFormularioValido();

    cy.contains('button[type="submit"], button', 'Registrar ocorrência').click();
    cy.wait('@registro').its('response.statusCode').should('eq', 201);
    cy.get('.alerta.sucesso').should('contain.text', 'SGOPI-').invoke('text').should('match', PROTOCOLO);
  });

  it('não envia sem a coordenada do fato', () => {
    cy.intercept('POST', '/v1/ocorrencias').as('registro');
    cy.login('agente', '/registrar');
    cy.contains('label', 'Natureza da ocorrência').find('input').type('Furto de veículo');
    cy.contains('label', 'Endereço').find('input').type('Av. Brasil, 500');
    cy.get('form.form textarea').first().type('Furto de veículo estacionado em via pública.');
    cy.get('fieldset input[type="text"]').first().type('Maria da Silva');
    cy.contains('button', 'Adicionar envolvido').click();

    cy.contains('button[type="submit"], button', 'Registrar ocorrência').click();
    cy.get('.alerta.erro').should('be.visible');
    cy.get('@registro.all').should('have.length', 0);
  });

  it('rejeita descrição com menos de 20 caracteres sem chamar a API', () => {
    cy.intercept('POST', '/v1/ocorrencias').as('registro');
    cy.login('agente', '/registrar');
    preencherFormularioValido();
    cy.get('form.form textarea').first().clear().type('curta');

    cy.contains('button[type="submit"], button', 'Registrar ocorrência').click();
    cy.get('.alerta.erro').should('be.visible');
    cy.get('@registro.all').should('have.length', 0);
  });

  it('exige ao menos um envolvido', () => {
    cy.intercept('POST', '/v1/ocorrencias').as('registro');
    cy.login('agente', '/registrar');
    cy.contains('label', 'Natureza da ocorrência').find('input').type('Furto de veículo');
    cy.contains('label', 'Endereço').find('input').type('Av. Brasil, 500');
    cy.get('input[type="number"]').eq(0).type('-29.7833');
    cy.get('input[type="number"]').eq(1).type('-55.7919');
    cy.get('form.form textarea').first().type('Furto de veículo estacionado em via pública.');

    cy.contains('button[type="submit"], button', 'Registrar ocorrência').click();
    cy.get('.alerta.erro').should('be.visible');
    cy.get('@registro.all').should('have.length', 0);
  });

  it('exibe o erro devolvido pela API quando o backend recusa o registro', () => {
    cy.intercept('POST', '/v1/ocorrencias', {
      statusCode: 422,
      body: { detail: 'A descrição deve ter ao menos 20 caracteres', code: 'ocorrencia.descricao_curta', request_id: null },
    }).as('registro');
    cy.login('agente', '/registrar');
    preencherFormularioValido();

    cy.contains('button[type="submit"], button', 'Registrar ocorrência').click();
    cy.wait('@registro');
    cy.contains('.toast', 'A descrição deve ter ao menos 20 caracteres').should('be.visible');
  });

  it('a ocorrência registrada aparece em "Minhas ocorrências" aguardando revisão', () => {
    cy.criarOcorrenciaApi().then((o) => {
      cy.login('agente', '/minhas');
      cy.contains('.lista.clicavel li', o.numero_protocolo)
        .should('be.visible')
        .and('contain.text', 'Aguardando revisão');
    });
  });

  it('operador não acessa a página de registro', () => {
    cy.login('operador', '/registrar');
    cy.url().should('not.include', '/registrar');
  });
});
