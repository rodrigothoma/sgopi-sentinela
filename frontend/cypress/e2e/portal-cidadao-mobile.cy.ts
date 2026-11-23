const LARGURA_MOBILE = 390;

const LOCALIZACAO_LONGA =
  'Avenida Brasil, número 500, bairro Centro, Alegrete, Rio Grande do Sul, próximo à praça central e ao terminal de ônibus municipal, com referência no estabelecimento comercial de esquina';

const NATUREZA_LONGA =
  'Furto qualificado de veículo automotor em via pública com concurso de agentes e emprego de arma de fogo, conforme circunstâncias apuradas no boletim';

const DOCUMENTO_AUTENTICADO = {
  numero_protocolo: 'SGOPI-2026-000140',
  situacao: 'AUTENTICO',
  chave_autenticidade: 'A'.repeat(24),
  chave_formatada: 'AAAA-AAAA-AAAA-AAAA-AAAA-AAAA',
  emitido_em: '2026-11-23T10:00:00.000Z',
  consultado_em: '2026-11-23T10:05:00.000Z',
  natureza: NATUREZA_LONGA,
  data_hora_fato: '2026-11-22T18:00:00.000Z',
  status_ocorrencia: 'VALIDADA',
  hash_integridade: 'a'.repeat(64),
  tipificacoes: [{ artigo: 'Art. 155 CP', descricao: 'Furto qualificado' }],
  envolvidos_por_tipo: { VITIMA: 1 },
  quantidade_evidencias: 2,
};

function expectSemOverflowHorizontal() {
  cy.window().then((win) => {
    expect(win.document.documentElement.scrollWidth, 'largura do documento').to.be.at.most(LARGURA_MOBILE + 1);
    expect(win.document.body.scrollWidth, 'largura do body').to.be.at.most(LARGURA_MOBILE + 1);
  });
}

function expectDentroDaViewport(seletor: string) {
  cy.get(seletor).each(($elemento) => {
    const retangulo = $elemento[0].getBoundingClientRect();
    expect(retangulo.left, `esquerda de ${seletor}`).to.be.at.least(-1);
    expect(retangulo.right, `direita de ${seletor}`).to.be.at.most(LARGURA_MOBILE + 1);
  });
}

describe('Portal cidadão no mobile', () => {
  beforeEach(() => {
    cy.viewport(LARGURA_MOBILE, 844);
  });

  it('mantém a landing sem cortes e com o título animado dentro da tela', () => {
    cy.visit('/');

    cy.get('.landing-hero').should('be.visible');
    cy.get('.split-flap-text').should('be.visible');
    cy.window().then((win) => {
      cy.get('.split-flap-text').then(($flap) => {
        expect(win.getComputedStyle($flap[0]).fontSize, 'tamanho da fonte no mobile').to.eq('26px');
        expect($flap[0].scrollWidth, 'rolagem interna do título').to.be.at.most($flap[0].clientWidth + 1);
      });
    });
    expectDentroDaViewport('.topbar, .topbar nav, .topbar nav a, .brand, .userbox, .hero-actions .btn, .hero-search-form');
    expectSemOverflowHorizontal();
  });

  it('mantém o formulário público de registro utilizável no mobile', () => {
    cy.visit('/registrar-cidadao');

    cy.get('form.form').should('be.visible');
    cy.get('.mapa').should('exist');
    expectDentroDaViewport('.form.card, fieldset, .grid2 input, .grid2 .glide-select-root, .mapa');
    expectSemOverflowHorizontal();
  });

  it('mantém o resultado da consulta legível com natureza e endereço longos', () => {
    cy.intercept('POST', '/v1/ocorrencias/publico/consulta', {
      statusCode: 200,
      body: {
        numero_protocolo: 'SGOPI-2026-000140',
        status: 'AGUARDANDO_REVISAO',
        natureza: NATUREZA_LONGA,
        localizacao: LOCALIZACAO_LONGA,
        criada_em: '2026-11-23T10:00:00.000Z',
      },
    }).as('consulta');

    cy.visit('/consulta');
    cy.get('form input').eq(0).type('SGOPI-2026-000140');
    cy.get('form input').eq(1).type('ABC123');
    cy.get('form button[type="submit"]').click();
    cy.wait('@consulta');

    cy.get('.grid2 dd').should('contain.text', LOCALIZACAO_LONGA);
    expectDentroDaViewport('.portal-wrap main.pagina, .card, form input, .grid2 dt, .grid2 dd, .btn-ghost');
    expectSemOverflowHorizontal();
  });

  it('mantém o espelho de autenticação legível com hash e natureza longos', () => {
    cy.intercept('GET', '/v1/publico/documentos/*', {
      statusCode: 200,
      body: DOCUMENTO_AUTENTICADO,
    }).as('autenticar');

    cy.visit(`/autenticar/${DOCUMENTO_AUTENTICADO.chave_autenticidade}`);
    cy.wait('@autenticar');

    cy.get('[data-cy="espelho-documento"]').should('be.visible');
    expectDentroDaViewport('.espelho-documento .grid2 dt, .espelho-documento .grid2 dd, .espelho-hash, .btn-ghost');
    expectSemOverflowHorizontal();
  });
});
