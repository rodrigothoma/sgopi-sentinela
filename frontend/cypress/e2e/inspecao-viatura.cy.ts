/// <reference types="cypress" />
import type { Viatura } from '../../src/types/api';

// Integração da interface com REST e WebSocket controlados: não altera o banco local.
const instante = new Date().toISOString();
const unidade = (id: string, prefixo: string): Viatura => ({
  id, prefixo, placa: 'ABC1D23', situacao: 'DISPONIVEL', sinal: 'OK',
  latitude: id === 'v1' ? -29.7833 : -29.789, longitude: id === 'v1' ? -55.7919 : -55.798, posicao_registrada_em: instante, versao: 1,
});
let frota: Viatura[];
let emitir: (tipo: string, dados: Record<string, unknown>) => void;
let interromper: () => void;

function abrirPainel(tilesIndisponiveis = false): void {
  cy.intercept('GET', '**/v1/viaturas', (req) => req.reply(frota)).as('frota');
  cy.intercept('GET', /\/v1\/ocorrencias(?:\?|$)/, {
    itens: [{ ocorrencia_id: 'oc-1', numero_protocolo: 'SGOPI-TESTE-1', natureza: 'Furto', localizacao: 'Centro',
      latitude: -29.78, longitude: -55.79, status: 'VALIDADA', prioridade: 'ALTA', criada_em: instante, atualizada_em: instante }], total: 1,
  });
  cy.intercept('GET', '**/v1/ocorrencias/oc-1/sugestoes-viaturas', { ocorrencia_id: 'oc-1', sugestoes: [], sem_elegiveis: true, disponiveis_sem_posicao: [] });
  cy.intercept('GET', '**/v1/despachos*', []);
  cy.intercept('GET', '**/v1/inteligencia/areas-risco*', []);
  cy.intercept('GET', '**/v1/simulador', { ligado: false, ticks: 0, orquestrador: { ligado: false } });
  cy.intercept('GET', /\/v1\/notificacoes(?:\/|\?|$)/, { itens: [], nao_lidas: 0, total: 0 });
  cy.intercept('GET', /tile\.openstreetmap\.org/, tilesIndisponiveis
    ? { statusCode: 503 }
    : { headers: { 'content-type': 'image/png' }, fixture: 'tile-transparente.png,null' });
  cy.visit('/painel', {
    onBeforeLoad(win) {
      win.localStorage.setItem('sgopi.idioma', 'pt');
      win.sessionStorage.setItem('sgopi.sessao', JSON.stringify({
        token: 'token-de-teste', expira_em: new Date(Date.now() + 3600000).toISOString(),
        usuario: { id: 'operador-teste', login: 'operador', nome: 'Operador de teste', papel: 'OPERADOR_CENTRAL' },
      }));
      class SocketDeTeste {
        static OPEN = 1;
        readyState = 1;
        onopen: (() => void) | null = null;
        onclose: ((evento: { code: number }) => void) | null = null;
        onmessage: ((evento: { data: string }) => void) | null = null;
        onerror: (() => void) | null = null;
        constructor() {
          emitir = (tipo, dados) => this.onmessage?.({ data: JSON.stringify({ tipo, dados, ocorrido_em: new Date().toISOString() }) });
          interromper = () => this.onclose?.({ code: 1006 });
          win.setTimeout(() => this.onopen?.(), 0);
        }
        send(): void {}
        close(): void { this.onclose?.({ code: 1000 }); }
      }
      (win as unknown as { WebSocket: typeof SocketDeTeste }).WebSocket = SocketDeTeste;
    },
  });
  cy.wait('@frota');
}

const inspecionar = (prefixo: string): void => {
  cy.get('[data-cy="inspecionar-viatura"]').contains(prefixo).click();
};

describe('Inspeção de viatura no painel (RF02)', () => {
  beforeEach(() => { cy.viewport(1200, 900); frota = [unidade('v1', 'VTR-01'), unidade('v2', 'VTR-02')]; });

  it('seleciona na frota e no mapa, destaca uma única unidade e permite fechar', () => {
    abrirPainel();
    inspecionar('VTR-01');
    cy.get('[data-cy="inspecao-viatura"]').should('contain.text', 'VTR-01').and('contain.text', 'ABC1D23');
    cy.get('.marker-viatura-selecionada').should('have.length', 1).and('have.attr', 'data-viatura-id', 'v1');
    cy.get('[data-viatura-id="v2"]').click();
    cy.get('[data-cy="inspecao-viatura"]').should('contain.text', 'VTR-02');
    cy.get('[data-cy="inspecionar-viatura"]').contains('VTR-02').should('have.attr', 'aria-pressed', 'true');
    cy.get('[data-cy="fechar-inspecao"]').click();
    cy.get('[data-cy="inspecao-viatura"]').should('not.exist');
    cy.get('.marker-viatura-selecionada').should('not.exist');
  });

  it('atualiza por evento e preserva a ocorrência selecionada', () => {
    abrirPainel();
    cy.contains('.lista.clicavel li', 'SGOPI-TESTE-1').click();
    inspecionar('VTR-01');
    cy.then(() => emitir('PosicaoAtualizada', { viatura_id: 'v1', latitude: -29.77, longitude: -55.78, registrada_em: instante, situacao: 'EM_DESLOCAMENTO' }));
    cy.get('[data-cy="inspecao-coordenadas"]').should('contain.text', '-29.77000, -55.78000');
    cy.get('[data-cy="inspecao-viatura"] .badge-EM_DESLOCAMENTO').should('exist');
    cy.contains('.lista.clicavel li.ativo', 'SGOPI-TESTE-1').should('exist');
    cy.get('.leaflet-map-pane').invoke('attr', 'style').then((antes) => {
      cy.get('[data-cy="centralizar-viatura"]').click();
      cy.get('.leaflet-map-pane').should(($pane) => expect($pane.attr('style')).not.to.equal(antes));
    });
    cy.get('[data-cy="centralizar-viatura"]').click();
    cy.get('[data-cy="inspecao-viatura"]').should('contain.text', 'VTR-01');
    cy.get('[data-cy="inspecao-viatura"]').then(($card) => {
      expect($card[0].getBoundingClientRect().right).to.be.at.most($card[0].ownerDocument.documentElement.clientWidth);
    });
    cy.get('[data-cy="inspecao-viatura"]').screenshot('inspecao-viatura-card');
    cy.scrollTo('top');
    cy.screenshot('inspecao-viatura-evento', { capture: 'viewport' });
  });

  it('explica falta de posição e indisponibilidade do mapa', () => {
    frota[0] = { ...frota[0], latitude: null, longitude: null, posicao_registrada_em: null, sinal: 'SEM_POSICAO' };
    abrirPainel(true);
    inspecionar('VTR-01');
    cy.get('[data-cy="centralizar-viatura"]').should('be.disabled');
    cy.get('[data-cy="inspecao-viatura"]').should('contain.text', 'Sem coordenadas');
    cy.get('[data-viatura-id="v1"]').should('not.exist');
    inspecionar('VTR-02');
    cy.get('[data-cy="inspecao-viatura"]').should('contain.text', 'O mapa está indisponível');
    cy.get('[data-cy="centralizar-viatura"]').should('be.disabled');
  });

  it('mantém GPS desatualizado e limpa seleção ao remover a unidade da carga', () => {
    frota[0] = { ...frota[0], sinal: 'SEM_SINAL' };
    abrirPainel();
    inspecionar('VTR-01');
    cy.get('[data-cy="inspecao-viatura"]').should('contain.text', 'última posição conhecida');
    cy.get('[data-cy="centralizar-viatura"]').should('not.be.disabled');
    cy.then(() => { frota = [unidade('v2', 'VTR-02')]; interromper(); });
    cy.wait('@frota');
    cy.get('[data-cy="inspecao-viatura"]').should('not.exist');
  });

  it('permite inspeção em largura reduzida com botões acessíveis', () => {
    abrirPainel();
    cy.viewport(390, 844);
    cy.get('[data-cy="inspecionar-viatura"]').first().focus().should('have.focus').click();
    cy.get('[data-cy="inspecao-viatura"]').scrollIntoView().should('be.visible');
    cy.screenshot('inspecao-viatura-mobile', { capture: 'viewport' });
    cy.get('[data-cy="fechar-inspecao"]').focus().should('have.focus').click();
    cy.get('[data-cy="inspecao-viatura"]').should('not.exist');
  });
});
