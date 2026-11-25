function expectSemOverflowHorizontal() {
  const larguraViewport = Cypress.config('viewportWidth');

  cy.window().then((win) => {
    expect(win.document.documentElement.scrollWidth).to.be.at.most(larguraViewport);
  });

  cy.get('.detalhe-pagina dl.grid2 dt, .detalhe-pagina dl.grid2 dd').each(($campo) => {
    const retangulo = $campo[0].getBoundingClientRect();
    expect(retangulo.left).to.be.at.least(0);
    expect(retangulo.right).to.be.at.most(larguraViewport);
  });

  cy.get('.detalhe-pagina .detalhe-abas').then(($abas) => {
    const retangulo = $abas[0].getBoundingClientRect();
    expect(retangulo.right).to.be.at.most(larguraViewport);
  });

  cy.get('.detalhe-pagina dl.grid2').then(($resumo) => {
    cy.window().then((win) => {
      const colunas = win.getComputedStyle($resumo[0]).gridTemplateColumns.trim().split(/\s+/);
      expect(colunas, 'colunas do resumo no mobile').to.have.length(1);
    });
  });

  cy.get('.detalhe-pagina .badge').first().then(($badge) => {
    cy.window().then((win) => {
      expect(win.getComputedStyle($badge[0]).whiteSpace).to.eq('normal');
    });
  });
}

const NATUREZA_LONGA = 'Furto qualificado de veículo automotor em via pública com concurso de agentes e emprego de arma de fogo, conforme circunstâncias apuradas no boletim';
const LOCALIZACAO_LONGA = 'Avenida Brasil, número 500, bairro Centro, Alegrete, Rio Grande do Sul, próximo à praça central e ao terminal de ônibus municipal, com referência no estabelecimento comercial de esquina';

describe('Separação lista/detalhe de ocorrências', () => {
  it('delegado abre o detalhe em rota própria e volta preservando filtros', () => {
    cy.criarOcorrenciaApi().then((o) => {
      cy.login('delegado', `/fila?protocolo=${encodeURIComponent(o.numero_protocolo)}`);
      cy.contains('.lista.clicavel li', o.numero_protocolo, { timeout: 15000 }).click();

      cy.url().should('match', new RegExp(`/fila/${o.ocorrencia_id}(\\?|$)`));
      cy.url().should('include', `protocolo=${encodeURIComponent(o.numero_protocolo)}`);
      cy.get('.detalhe').should('contain.text', o.numero_protocolo);
      cy.get('.lista.clicavel').should('not.exist');

      cy.contains('a', 'Voltar à fila').click();
      cy.url().should('match', /\/fila(\?|$)/).and('not.include', `/fila/${o.ocorrencia_id}`);
      cy.contains('.lista.clicavel li', o.numero_protocolo).should('be.visible');
    });
  });

  it('redireciona o link legado ?ocorrencia= para a rota de detalhe', () => {
    cy.criarOcorrenciaApi().then((o) => {
      cy.login('delegado', `/fila?ocorrencia=${o.ocorrencia_id}`);
      cy.url().should('include', `/fila/${o.ocorrencia_id}`);
      cy.get('.detalhe').should('contain.text', o.numero_protocolo);
    });
  });

  it('mantém o detalhe em largura integral e sem cortes no mobile', () => {
    cy.viewport(390, 844);
    cy.criarOcorrenciaApi({ natureza: NATUREZA_LONGA, localizacao: LOCALIZACAO_LONGA }).then((o) => {
      cy.login('agente', '/minhas');
      cy.contains('.lista.clicavel li', o.numero_protocolo, { timeout: 15000 }).click();

      cy.url().should('include', `/minhas/${o.ocorrencia_id}`);
      cy.get('.detalhe').should('be.visible').and('contain.text', o.numero_protocolo);
      cy.get('.lista.clicavel').should('not.exist');
      cy.get('.duas-colunas').should('not.exist');
      cy.get('.detalhe-pagina .card').then(($card) => {
        const larguraCartao = Number($card.width());
        cy.get('.detalhe').then(($detalhe) => {
          expect(Number($detalhe.width())).to.be.greaterThan(larguraCartao - 50);
        });
      });
      expectSemOverflowHorizontal();

      cy.contains('a', 'Voltar às ocorrências').click();
      cy.contains('.lista.clicavel li', o.numero_protocolo).should('be.visible');

      cy.login('delegado', '/fila');
      cy.contains('.lista.clicavel li', o.numero_protocolo, { timeout: 15000 }).click();

      cy.url().should('include', `/fila/${o.ocorrencia_id}`);
      cy.get('.detalhe').should('be.visible').and('contain.text', o.numero_protocolo);
      cy.get('.lista.clicavel').should('not.exist');
      expectSemOverflowHorizontal();
    });
  });
});
