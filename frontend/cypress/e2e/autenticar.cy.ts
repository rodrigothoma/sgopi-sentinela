/// <reference types="cypress" />

/**
 * RF08 — Testes E2E da autenticação pública de documentos (UC08).
 * Pré-requisito: backend (:8000) e frontend (:3000) rodando com o seed.
 */

const CHAVE_FORMATADA = /^[A-Z2-9]{4}(-[A-Z2-9]{4}){5}$/;

/** Registra como agente e valida como delegado → documento emitido com chave e hash. */
function emitirDocumento() {
  return cy.criarOcorrenciaApi().then((o) =>
    cy.apiComo('delegado', 'POST', `/v1/ocorrencias/${o.ocorrencia_id}/validar`).then((r) => {
      expect(r.status).to.eq(200);
      const corpo = r.body as { chave_autenticidade: string; hash_narrativa: string };
      return { ...o, chave: corpo.chave_autenticidade, hash: corpo.hash_narrativa };
    }),
  );
}

describe('RF08 — Comprovante de ocorrência com QR Code', () => {
  it('agente vê a chave após a validação e emite o comprovante com QR Code legível', () => {
    emitirDocumento().then((doc) => {
      cy.login('agente', '/minhas');
      cy.contains('.lista.clicavel li', doc.numero_protocolo).click();
      cy.get('[data-cy="documento-emitido"]').should('be.visible');
      cy.get('[data-cy="chave-autenticidade"]').invoke('text').should('match', CHAVE_FORMATADA);

      cy.get('[data-cy="emitir-comprovante"]').click();
      cy.get('[data-cy="comprovante-ocorrencia"]').should('be.visible')
        .and('contain.text', doc.numero_protocolo)
        .and('contain.text', `/autenticar/${doc.chave}`)
        .and('contain.text', doc.hash);
      cy.get('[data-cy="comprovante-chave"]').invoke('text').should('match', CHAVE_FORMATADA);
      cy.get('[data-cy="comprovante-qr"] svg').should('be.visible');
      cy.get('[data-cy="comprovante-qr"] svg path').should('have.length.greaterThan', 0);
      cy.screenshot('rf08-comprovante', { capture: 'viewport' });
    });
  });

  it('ocorrência ainda não validada não possui comprovante', () => {
    cy.criarOcorrenciaApi().then((o) => {
      cy.login('agente', '/minhas');
      cy.contains('.lista.clicavel li', o.numero_protocolo).click();
      cy.get('.detalhe').should('contain.text', o.numero_protocolo);
      cy.get('[data-cy="documento-emitido"]').should('not.exist');
    });
  });
});

describe('RF08 — Página pública /autenticar', () => {
  it('abre pelo link do QR Code e certifica DOCUMENTO AUTÊNTICO sem login', () => {
    emitirDocumento().then((doc) => {
      cy.intercept('GET', '/v1/publico/documentos/*').as('autenticar');
      cy.visit(`/autenticar/${doc.chave}`);
      cy.wait('@autenticar').then(({ request, response }) => {
        expect(request.headers).to.not.have.property('authorization');
        expect(response?.statusCode).to.eq(200);
      });
      cy.get('[data-cy="veredito"]').should('have.attr', 'data-veredito', 'AUTENTICO').and('contain.text', 'DOCUMENTO AUTÊNTICO');
      cy.get('[data-cy="espelho-documento"]').should('contain.text', doc.numero_protocolo).and('contain.text', doc.hash);
      // LGPD: nada de nome/CPF da envolvida do seed (criarOcorrenciaApi usa "Maria")
      cy.get('[data-cy="espelho-documento"]').should('not.contain.text', 'Maria');
      cy.screenshot('rf08-autentico');
    });
  });

  it('aceita a chave digitada com hífens/minúsculas e o hash SHA-256', () => {
    emitirDocumento().then((doc) => {
      const digitada = doc.chave.match(/.{4}/g)!.join('-').toLowerCase();
      cy.visit('/autenticar');
      cy.get('[data-cy="autenticar-codigo"]').type(digitada);
      cy.get('[data-cy="autenticar-botao"]').click();
      cy.get('[data-cy="veredito"]').should('have.attr', 'data-veredito', 'AUTENTICO');
      cy.location('pathname').should('eq', `/autenticar/${doc.chave}`);

      cy.get('[data-cy="autenticar-codigo"]').clear().type(doc.hash);
      cy.get('[data-cy="autenticar-botao"]').click();
      cy.get('[data-cy="veredito"]').should('have.attr', 'data-veredito', 'AUTENTICO');
      cy.get('[data-cy="espelho-documento"]').should('contain.text', doc.numero_protocolo);
    });
  });

  it('chave desconhecida exibe NÃO RECONHECIDO e código curto exibe CÓDIGO INVÁLIDO', () => {
    cy.visit('/autenticar');
    cy.get('[data-cy="autenticar-codigo"]').type('ZZZZ-ZZZZ-ZZZZ-ZZZZ-ZZZZ-ZZZZ');
    cy.get('[data-cy="autenticar-botao"]').click();
    cy.get('[data-cy="veredito"]').should('have.attr', 'data-veredito', 'NAO_RECONHECIDO').and('contain.text', 'NÃO RECONHECIDO');
    cy.get('[data-cy="espelho-documento"]').should('not.exist');
    cy.screenshot('rf08-nao-reconhecido');

    cy.get('[data-cy="autenticar-codigo"]').clear().type('ABC-123');
    cy.get('[data-cy="autenticar-botao"]').click();
    cy.get('[data-cy="veredito"]').should('have.attr', 'data-veredito', 'CODIGO_INVALIDO');
  });
});
