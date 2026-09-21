/// <reference types="cypress" />

/**
 * RF03 — Testes E2E de apreensões e cadeia de custódia (UC03).
 * Pré-requisito: backend (:8000) e frontend (:3000) rodando com o seed.
 */

const PROTOCOLO = /SGOPI-\d{4}-\d{6}/;
const lacreUnico = (sufixo = '') => `LC-${Date.now().toString(36).toUpperCase()}${sufixo}`;

/** Preenche o boletim mínimo válido (coordenada pelos campos numéricos). */
function preencherBoletimValido() {
  cy.contains('label', 'Natureza da ocorrência').find('input').type('Porte ilegal de arma');
  cy.get('#localizacao').type('Av. Brasil, 500 — Alegrete/RS');
  cy.contains('summary', 'Informar coordenadas manualmente').click();
  cy.get('input[type="number"]').eq(0).type('-29.7833');
  cy.get('input[type="number"]').eq(1).type('-55.7919');
  cy.get('form.form textarea').first().type('Abordagem em via pública com apreensão de arma de fogo e entorpecente.');
  cy.get('fieldset input[type="text"]').first().type('Fulano de Tal');
  cy.contains('button', 'Adicionar envolvido').click();
}

/** Preenche o subformulário de item apreendido (dentro do container informado). */
function preencherItem(lacre: string, opts: { tipo?: string; marca?: string; calibre?: string } = {}) {
  cy.get('[data-cy="item-apreendido-form"]').within(() => {
    cy.get('#apreensao-tipo').select(opts.tipo ?? 'OBJETO');
    cy.get('#apreensao-descricao').clear().type('Revólver Taurus com 5 munições');
    cy.get('#apreensao-quantidade').clear().type('1');
    cy.get('#apreensao-estado').select('BOM');
    cy.get('#apreensao-lacre').clear().type(lacre);
    if (opts.marca) cy.get('#apreensao-marca').clear().type(opts.marca);
    if (opts.calibre) cy.get('#apreensao-calibre').clear().type(opts.calibre);
    cy.get('#apreensao-localizacao').clear().type('Cofre 2 — prateleira B');
  });
}

function abrirAbaApreensoes(protocolo: string) {
  cy.contains('.lista.clicavel li', protocolo).click();
  cy.get('.detalhe').should('contain.text', protocolo);
  cy.get('[data-cy="tab-apreensoes"]').click();
  cy.get('[data-cy="aba-apreensoes"]').should('be.visible');
}

describe('RF03 — Apreensões no registro da ocorrência', () => {
  it('registra a ocorrência já com item apreendido pela seção opcional', () => {
    cy.intercept('POST', '/v1/ocorrencias').as('registro');
    cy.login('agente', '/registrar');
    preencherBoletimValido();

    cy.get('[data-cy="toggle-apreensoes"]').check();
    const lacre = lacreUnico();
    preencherItem(lacre, { tipo: 'ARMA_DE_FOGO', marca: 'Taurus', calibre: '.38' });
    cy.contains('button', 'Adicionar item').click();
    cy.get('[data-cy="secao-apreensoes"] .lista').should('contain.text', lacre);

    cy.contains('button[type="submit"], button', 'Registrar ocorrência').click();
    cy.wait('@registro').then(({ request, response }) => {
      expect(response?.statusCode).to.eq(201);
      expect(request.body.itens_apreendidos).to.have.length(1);
      expect(request.body.itens_apreendidos[0].numero_lacre).to.eq(lacre);
    });
    cy.get('.alerta.sucesso').invoke('text').should('match', PROTOCOLO);
  });

  it('bloqueia arma de fogo sem marca/calibre e lacre repetido antes de chamar a API', () => {
    cy.login('agente', '/registrar');
    cy.get('[data-cy="toggle-apreensoes"]').check();
    const lacre = lacreUnico('-DUP');
    preencherItem(lacre, { tipo: 'ARMA_DE_FOGO' });
    cy.contains('button', 'Adicionar item').click();
    cy.get('[data-cy="item-apreendido-form"] .campo-erro').should('contain.text', 'marca e calibre');

    preencherItem(lacre, { tipo: 'OBJETO' });
    cy.contains('button', 'Adicionar item').click();
    cy.get('[data-cy="secao-apreensoes"] .lista li').should('have.length', 1);
    preencherItem(lacre, { tipo: 'OBJETO' });
    cy.contains('button', 'Adicionar item').click();
    cy.get('[data-cy="item-apreendido-form"] .campo-erro').should('contain.text', 'lacre já foi usado');
  });
});

describe('RF03 — Aba de apreensões no detalhe da ocorrência', () => {
  it('agente registra item, transfere custódia e emite o Auto de Apreensão', () => {
    cy.intercept('POST', '/v1/ocorrencias/*/apreensoes').as('registrarItem');
    cy.intercept('POST', '/v1/ocorrencias/*/apreensoes/*/movimentacoes').as('movimentar');
    cy.intercept('GET', '/v1/ocorrencias/*/auto-apreensao').as('auto');

    cy.criarOcorrenciaApi().then((o) => {
      cy.login('agente', '/minhas');
      abrirAbaApreensoes(o.numero_protocolo);
      cy.get('[data-cy="emitir-auto"]').should('be.disabled');

      const lacre = lacreUnico('-A');
      preencherItem(lacre, { tipo: 'ENTORPECENTE' });
      cy.contains('button', 'Registrar apreensão').click();
      cy.wait('@registrarItem').its('response.statusCode').should('eq', 201);
      cy.get('[data-cy="apreensao-item"]').should('have.length', 1).and('contain.text', lacre);
      cy.get('[data-cy="tab-apreensoes"]').should('contain.text', '(1)');

      cy.get('[data-cy="apreensao-item"]').first().within(() => {
        cy.get('input[aria-label="Novo local de custódia"]').type('Perícia — IGP');
        cy.contains('button', 'Transferir custódia').click();
      });
      cy.wait('@movimentar').its('response.statusCode').should('eq', 201);
      cy.get('[data-cy="apreensao-item"]').first().should('contain.text', 'Perícia — IGP');

      cy.get('[data-cy="emitir-auto"]').click();
      cy.wait('@auto').its('response.statusCode').should('eq', 200);
      cy.get('[data-cy="auto-apreensao"]').should('be.visible')
        .and('contain.text', `AA-${o.numero_protocolo}`)
        .and('contain.text', lacre)
        .and('contain.text', 'Perícia — IGP')
        .and('contain.text', 'SHA-256');
    });
  });

  it('delegado vê os itens na aba mas não vê o cadastro', () => {
    cy.criarOcorrenciaApi({
      itens_apreendidos: [{
        tipo: 'VEICULO', descricao: 'Motocicleta Honda CG 160', quantidade: 1, unidade: 'UNIDADE',
        estado_conservacao: 'REGULAR', numero_lacre: lacreUnico('-V'), localizacao_deposito: 'Pátio 1',
      }],
    }).then((o) => {
      cy.login('delegado', '/fila');
      abrirAbaApreensoes(o.numero_protocolo);
      cy.get('[data-cy="apreensao-item"]').should('have.length', 1).and('contain.text', 'Motocicleta');
      cy.get('[data-cy="item-apreendido-form"]').should('not.exist');
      cy.contains('button', 'Transferir custódia').should('exist');
    });
  });
});
