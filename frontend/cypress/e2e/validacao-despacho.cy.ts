/// <reference types="cypress" />

/**
 * Issue #22 — Testes E2E de validação (UC04) e despacho tático (UC02).
 * Pré-requisito: backend (:8000) e frontend (:3000) rodando com o seed
 * (agente/delegado/operador e 5 viaturas).
 */

const JUSTIFICATIVA = 'Narrativa incompleta: informar placa e características do veículo.';

function validarPelaApi(ocorrenciaId: string) {
  cy.apiComo('delegado', 'POST', `/v1/ocorrencias/${ocorrenciaId}/validar`).its('status').should('eq', 200);
}

/** Garante posições de GPS recentes: liga o simulador (idempotente) e aguarda alguns ticks. */
function garantirPosicoesGps() {
  cy.apiComo('operador', 'POST', '/v1/simulador/ligar');
  // eslint-disable-next-line cypress/no-unnecessary-waiting
  cy.wait(3000);
}

function abrirNaFila(protocolo: string) {
  cy.contains('.lista.clicavel li', protocolo).click();
  cy.get('.detalhe').should('contain.text', protocolo);
}

describe('Issue #22 — Validação pelo Delegado (UC04)', () => {
  it('delegado valida a ocorrência e ela sai da fila', () => {
    cy.criarOcorrenciaApi().then((o) => {
      cy.login('delegado', '/fila');
      abrirNaFila(o.numero_protocolo);
      cy.contains('button', 'Validar').click();
      cy.contains('.toast', 'validada', { matchCase: false }).should('be.visible');
      cy.get('.detalhe').should('contain.text', 'Validada');
      // sai do filtro "Aguardando revisão"
      cy.contains('.lista.clicavel li', o.numero_protocolo).should('not.exist');
      // aparece no filtro "Validadas / em atendimento"
      cy.contains('.tabs .tab', 'Validadas').click();
      cy.contains('.lista.clicavel li', o.numero_protocolo).should('be.visible');
    });
  });

  it('bloqueia devolução com justificativa curta', () => {
    cy.criarOcorrenciaApi().then((o) => {
      cy.login('delegado', '/fila');
      abrirNaFila(o.numero_protocolo);
      cy.get('textarea').type('curta');
      cy.contains('button', 'Devolver para correção').click();
      cy.contains('.toast', '10 caracteres').should('be.visible');
      cy.get('.detalhe').should('contain.text', 'Aguardando revisão');
    });
  });

  it('delegado devolve, agente corrige e reenvia para revisão (RF04)', () => {
    cy.criarOcorrenciaApi().then((o) => {
      // Delegado devolve
      cy.login('delegado', '/fila');
      abrirNaFila(o.numero_protocolo);
      cy.get('textarea').type(JUSTIFICATIVA);
      cy.contains('button', 'Devolver para correção').click();
      cy.get('.detalhe').should('contain.text', 'Em correção');

      // Agente corrige e reenvia
      cy.login('agente', '/minhas');
      cy.contains('.lista.clicavel li', o.numero_protocolo).click();
      cy.get('.detalhe').should('contain.text', JUSTIFICATIVA);
      cy.contains('button', 'Editar').click();
      cy.get('textarea').first().clear().type('Furto de veículo em via pública; placa ABC-1234, cor prata.');
      cy.contains('button', 'Salvar correção').click();
      cy.contains('button', 'Reenviar para revisão').click();
      cy.get('.detalhe').should('contain.text', 'Aguardando revisão');
    });
  });

  it('delegado rejeita a ocorrência (terminal)', () => {
    cy.criarOcorrenciaApi().then((o) => {
      cy.on('window:confirm', () => true);
      cy.login('delegado', '/fila');
      abrirNaFila(o.numero_protocolo);
      cy.get('textarea').type('Fato atípico, sem materialidade delitiva.');
      cy.contains('button', 'Rejeitar').click();
      cy.get('.detalhe').should('contain.text', 'Rejeitada');
      cy.contains('.tabs .tab', 'Rejeitadas').click();
      cy.contains('.lista.clicavel li', o.numero_protocolo).should('be.visible');
    });
  });

  it('agente não acessa a fila de revisão', () => {
    cy.login('agente', '/fila');
    cy.url().should('not.include', '/fila');
  });
});

describe('Issue #22 — Despacho tático (UC02)', () => {
  before(() => {
    // Limpa ordens ativas de runs anteriores (viaturas EM_DESLOCAMENTO) para garantir frota DISPONIVEL
    cy.limparOrdensAtivas();
  });

  it('operador despacha a viatura mais próxima e encerra o atendimento', () => {
    cy.criarOcorrenciaApi().then((o) => {
      validarPelaApi(o.ocorrencia_id);
      garantirPosicoesGps();

      cy.login('operador', '/painel');
      cy.contains('.lista.clicavel li', o.numero_protocolo).click();

      // sugestões ordenadas pela proximidade
      cy.contains('section.card h3', `Despachar ${o.numero_protocolo}`);
      cy.contains('h3', 'Despachar').closest('section').find('.lista li', { timeout: 15000 })
        .first()
        .should('contain.text', '#1');
      cy.contains('h3', 'Despachar').closest('section').find('.lista li').first()
        .contains('button', 'Despachar').click();
      cy.contains('.toast', 'Ordem de despacho').should('be.visible');
      cy.contains('.lista.clicavel li', o.numero_protocolo).should('contain.text', 'Em atendimento');

      // encerramento
      cy.contains('.lista.clicavel li', o.numero_protocolo).click();
      cy.contains('.card h3', `Atendimento ${o.numero_protocolo}`);
      cy.get('.painel-lateral textarea').type('Fato atendido no local; boletim emitido.');
      cy.contains('button', 'Encerrar atendimento').click();
      cy.contains('.toast', 'Atendimento encerrado').should('be.visible');
      cy.contains('.lista.clicavel li', o.numero_protocolo).should('not.exist');
    });
  });

  it('o botão de encerrar fica desabilitado sem desfecho', () => {
    cy.criarOcorrenciaApi().then((o) => {
      validarPelaApi(o.ocorrencia_id);
      garantirPosicoesGps();
      // despacha a 1ª sugestão via API
      cy.apiComo('operador', 'GET', `/v1/ocorrencias/${o.ocorrencia_id}/sugestoes-viaturas`).then((r) => {
        const sugestoes = (r.body as { sugestoes: { viatura: { id: string } }[] }).sugestoes;
        expect(sugestoes.length, 'deve haver ao menos uma viatura elegível (rode e2e:db se vazio)').to.be.greaterThan(0);
        cy.apiComo('operador', 'POST', '/v1/despachos', {
          ocorrencia_id: o.ocorrencia_id,
          viatura_id: sugestoes[0].viatura.id,
        }).its('status').should('eq', 201);
      });

      cy.login('operador', '/painel');
      cy.contains('.lista.clicavel li', o.numero_protocolo).click();
      cy.contains('button', 'Encerrar atendimento').should('be.disabled');
    });
  });

  it('exibe o aviso de fallback quando não há viatura elegível', () => {
    cy.criarOcorrenciaApi().then((o) => {
      validarPelaApi(o.ocorrencia_id);
      // marca todas as viaturas como INDISPONIVEL via API
      cy.apiComo('operador', 'GET', '/v1/viaturas').then((r) => {
        const viaturas = (r.body as { id: string }[]);
        viaturas.forEach((v) => {
          cy.apiComo('operador', 'PATCH', `/v1/viaturas/${v.id}/situacao`, { situacao: 'INDISPONIVEL' });
        });
      });

      cy.login('operador', '/painel');
      cy.contains('.lista.clicavel li', o.numero_protocolo).click();
      cy.contains('.alerta.aviso', 'Nenhuma viatura disponível', { timeout: 15000 }).should('be.visible');

      // limpeza: devolve as viaturas a DISPONIVEL
      cy.apiComo('operador', 'GET', '/v1/viaturas').then((r) => {
        (r.body as { id: string }[]).forEach((v) => {
          cy.apiComo('operador', 'PATCH', `/v1/viaturas/${v.id}/situacao`, { situacao: 'DISPONIVEL' });
        });
      });
    });
  });

  it('liga o simulador de GPS pelo painel', () => {
    cy.login('operador', '/painel');
    cy.get('.conexao').should('exist');
    cy.contains('.painel-barra button', /simulador/i).then(($btn) => {
      const ligado = /Desligar/.test($btn.text());
      if (!ligado) cy.wrap($btn).click();
      cy.contains('.painel-barra button', /Desligar simulador/, { timeout: 15000 }).should('be.visible');
    });
  });
});
