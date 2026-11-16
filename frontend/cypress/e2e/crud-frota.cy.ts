/// <reference types="cypress" />
import type { Viatura } from '../../src/types/api';

// REST/WS controlados: estes cenários não cadastram nem excluem viaturas do banco local.
let frota: Viatura[];
let emitir: (tipo: string, dados: Record<string, unknown>) => void;
const unidade = (): Viatura => ({ id: 'v1', prefixo: 'VTR-01', placa: 'ABC1D23', responsavel: 'Ana Souza', versao: 1,
  situacao: 'DISPONIVEL', sinal: 'SEM_POSICAO', latitude: null, longitude: null, posicao_registrada_em: null });

function abrir(caminho = '/frota'): void {
  cy.intercept('GET', '**/v1/viaturas', (req) => req.reply(frota)).as('frota');
  cy.intercept('POST', '**/v1/viaturas', (req) => {
    const v = { ...unidade(), ...req.body, id: 'nova' };
    frota.push(v); req.reply({ statusCode: 201, body: v });
  }).as('cadastrar');
  cy.intercept('PATCH', '**/v1/viaturas/v1', (req) => {
    frota[0] = { ...frota[0], ...req.body, versao: frota[0].versao + 1 }; req.reply(frota[0]);
  }).as('editar');
  cy.intercept('DELETE', '**/v1/viaturas/v1?versao=*', (req) => {
    frota = frota.filter((v) => v.id !== 'v1'); req.reply({ statusCode: 204 });
  }).as('excluir');
  cy.intercept('GET', /\/v1\/notificacoes(?:\/|\?|$)/, { itens: [], total: 0, nao_lidas: 0 });
  cy.intercept('GET', /\/v1\/ocorrencias(?:\?|$)/, { itens: [], total: 0 });
  cy.intercept('GET', '**/v1/despachos*', []);
  cy.intercept('GET', '**/v1/inteligencia/areas-risco*', []);
  cy.intercept('GET', '**/v1/simulador', { ligado: false, orquestrador: { ligado: false } });
  cy.intercept('GET', /tile\.openstreetmap\.org/, { headers: { 'content-type': 'image/png' }, fixture: 'tile-transparente.png,null' });
  cy.visit(caminho, {
    onBeforeLoad(win) {
      win.localStorage.setItem('sgopi.idioma', 'pt');
      win.sessionStorage.setItem('sgopi.sessao', JSON.stringify({ token: 'teste', expira_em: new Date(Date.now() + 3600000).toISOString(),
        usuario: { id: 'op', nome: 'Operador', login: 'operador', papel: 'OPERADOR_CENTRAL' } }));
      class SocketTeste {
        static OPEN = 1;
        readyState = 1;
        onopen: (() => void) | null = null;
        onclose: ((e: { code: number }) => void) | null = null;
        onmessage: ((e: { data: string }) => void) | null = null;
        onerror: (() => void) | null = null;
        constructor() {
          emitir = (tipo, dados) => this.onmessage?.({ data: JSON.stringify({ tipo, dados, ocorrido_em: new Date().toISOString() }) });
          win.setTimeout(() => this.onopen?.(), 0);
        }
        send(): void {}
        close(): void { this.onclose?.({ code: 1000 }); }
      }
      (win as unknown as { WebSocket: typeof SocketTeste }).WebSocket = SocketTeste;
    },
  });
  cy.wait('@frota');
}
const linha = () => cy.get('[data-cy="frota-viatura"]').first();

describe('Cadastro da frota', () => {
  beforeEach(() => { frota = [unidade()]; });

  it('cadastra sem responsável e edita identificação e responsável', () => {
    abrir();
    cy.get('[data-cy="frota-prefixo"]').type('VTR-02');
    cy.get('[data-cy="frota-placa"]').type('DEF4G56');
    cy.get('[data-cy="frota-salvar"]').click();
    cy.wait('@cadastrar').its('request.body.responsavel').should('be.null');
    cy.get('[data-cy="frota-viatura"]').last().should('contain.text', 'Sem responsável');
    linha().find('[data-cy="frota-editar"]').click();
    cy.get('[data-cy="frota-prefixo"]').clear().type('VTR-03');
    cy.get('[data-cy="frota-placa"]').clear().type('GHI7J89');
    cy.get('[data-cy="frota-responsavel"]').clear().type('Bruno Lima');
    cy.get('[data-cy="frota-salvar"]').click();
    cy.wait('@editar').its('request.body').should('deep.equal', { prefixo: 'VTR-03', placa: 'GHI7J89', responsavel: 'Bruno Lima', versao: 1 });
    linha().should('contain.text', 'VTR-03').and('contain.text', 'GHI7J89').and('contain.text', 'Bruno Lima');
    linha().find('[data-cy="frota-editar"]').click();
    cy.get('[data-cy="frota-responsavel"]').clear();
    cy.get('[data-cy="frota-salvar"]').click();
    cy.wait('@editar').its('request.body.responsavel').should('be.null');
    linha().should('contain.text', 'Sem responsável');
  });

  it('cancela edição e exige confirmação antes de excluir', () => {
    abrir();
    linha().find('[data-cy="frota-editar"]').click();
    cy.get('[data-cy="frota-prefixo"]').clear().type('RASCUNHO');
    cy.get('[data-cy="frota-cancelar"]').click();
    linha().should('contain.text', 'VTR-01');
    linha().find('[data-cy="frota-excluir"]').click();
    cy.get('[role="alertdialog"]').contains('button', 'Cancelar').should('have.focus').click();
    linha().should('exist');
    linha().find('[data-cy="frota-excluir"]').click();
    cy.get('[role="alertdialog"]').contains('button', 'Confirmar').click();
    cy.wait('@excluir').its('request.url').should('include', 'versao=1');
    cy.get('[data-cy="frota-viatura"]').should('not.exist');
  });

  it('preserva formulário em conflito e bloqueia exclusão em atendimento', () => {
    frota[0].situacao = 'OPERANDO';
    abrir();
    linha().find('[data-cy="frota-excluir"]').should('be.disabled');
    linha().find('[data-cy="frota-editar"]').click();
    cy.get('[data-cy="frota-responsavel"]').clear().type('Bruno Lima');
    cy.intercept('PATCH', '**/v1/viaturas/v1', { statusCode: 409, body: { detail: 'Recarregue a frota.', code: 'generic.versao_desatualizada' } }).as('conflito');
    cy.get('[data-cy="frota-salvar"]').click();
    cy.wait('@conflito');
    cy.get('[data-cy="frota-responsavel"]').should('have.value', 'Bruno Lima');
    linha().should('contain.text', 'Ana Souza');
  });

  it('atualiza responsável no card aberto por evento e fecha ao excluir a viatura', () => {
    frota[0] = { ...frota[0], latitude: -29.7833, longitude: -55.7919, sinal: 'OK', posicao_registrada_em: new Date().toISOString() };
    abrir('/painel');
    cy.get('[data-cy="inspecionar-viatura"]').contains('VTR-01').click();
    cy.get('[data-cy="inspecao-responsavel"]').should('have.text', 'Ana Souza');
    cy.then(() => { frota[0] = { ...frota[0], prefixo: 'VTR-EDIT', placa: 'NEW1234', responsavel: 'Bruno Lima' }; emitir('ViaturaCadastroAlterado', { viatura_id: 'v1' }); });
    cy.wait('@frota');
    cy.get('[data-cy="inspecao-responsavel"]').should('have.text', 'Bruno Lima');
    cy.get('[data-viatura-id="v1"]').should('have.attr', 'title', 'VTR-EDIT').trigger('mouseover');
    cy.get('.leaflet-tooltip').should('contain.text', 'VTR-EDIT · NEW1234');
    cy.then(() => { frota[0].responsavel = null; emitir('ViaturaCadastroAlterado', { viatura_id: 'v1' }); });
    cy.wait('@frota');
    cy.get('[data-cy="inspecao-responsavel"]').should('have.text', 'Sem responsável');
    cy.then(() => emitir('ViaturaExcluida', { viatura_id: 'v1' }));
    cy.get('[data-cy="inspecao-viatura"]').should('not.exist');
  });
});
