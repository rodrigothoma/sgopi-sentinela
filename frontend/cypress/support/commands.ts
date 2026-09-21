/// <reference types="cypress" />

type PapelLogin = 'agente' | 'delegado' | 'operador';

interface CorpoOcorrencia {
  natureza?: string;
  descricao?: string;
  localizacao?: string;
  latitude?: number;
  longitude?: number;
  data_hora_fato?: string;
  envolvidos?: { nome: string; tipo: string; documento?: string }[];
  tipificacoes?: { artigo: string; descricao: string }[];
}

declare global {
  // eslint-disable-next-line @typescript-eslint/no-namespace
  namespace Cypress {
    interface Chainable {
      /** Login rápido via API: grava a sessão no sessionStorage, sem passar pela tela. */
      login(perfil: PapelLogin, caminho?: string): Chainable<void>;
      /** Login digitando na tela de login (usado quando o login é o objeto do teste). */
      loginPelaTela(login: string, senha: string): Chainable<void>;
      /** Cria uma ocorrência via API autenticada como agente (setup de cenários). */
      criarOcorrenciaApi(overrides?: CorpoOcorrencia): Chainable<{ ocorrencia_id: string; numero_protocolo: string }>;
      /** Executa uma chamada REST autenticada como o perfil informado. */
      apiComo(perfil: PapelLogin, metodo: string, url: string, body?: unknown): Chainable<Cypress.Response<unknown>>;
      /** Encerra todas as ordens de despacho ativas (limpa viaturas EM_DESLOCAMENTO deixadas por runs anteriores). */
      limparOrdensAtivas(): Chainable<void>;
    }
  }
}

// Backend e seed padrão do ambiente local (ver README — seção Testes E2E).
const API_URL = 'http://localhost:8000';
const SENHA_SEED = 'Senha@123';
const api = () => API_URL;
const senhaPadrao = () => SENHA_SEED;

Cypress.Commands.add('apiComo', (perfil, metodo, url, body) =>
  cy
    .request('POST', `${api()}/v1/auth/login`, { login: perfil, senha: senhaPadrao() })
    .then((loginResp) =>
      cy.request({
        method: metodo,
        url: `${api()}${url}`,
        headers: { Authorization: `Bearer ${loginResp.body.access_token}` },
        body: body ?? undefined,
        failOnStatusCode: false,
      }),
    ) as unknown as Cypress.Chainable<Cypress.Response<unknown>>,
);

Cypress.Commands.add('login', (perfil, caminho = '/') => {
  cy.request('POST', `${api()}/v1/auth/login`, { login: perfil, senha: senhaPadrao() }).then((r) => {
    const sessao = { token: r.body.access_token, expira_em: r.body.expira_em, usuario: r.body.usuario };
    cy.visit(caminho, {
      onBeforeLoad(win) {
        win.sessionStorage.setItem('sgopi.sessao', JSON.stringify(sessao));
        win.localStorage.setItem('sgopi.idioma', 'pt');
      },
    });
  }) as unknown as Cypress.Chainable<void>;
});

Cypress.Commands.add('loginPelaTela', (login, senha) => {
  cy.visit('/login');
  cy.get('form.login input').first().clear().type(login);
  cy.get('form.login input[type="password"]').clear().type(senha);
  cy.get('form.login button').first().click();
});

Cypress.Commands.add('criarOcorrenciaApi', (overrides = {}) => {
  const corpo = {
    natureza: 'Furto',
    descricao: 'Furto de veículo em via pública, sem violência, durante a tarde.',
    localizacao: 'Av. Brasil, 500 — Alegrete/RS',
    latitude: -29.7833,
    longitude: -55.7919,
    data_hora_fato: new Date(Date.now() - 3600_000).toISOString(),
    envolvidos: [{ nome: 'Maria da Silva', tipo: 'VITIMA' }],
    tipificacoes: [{ artigo: 'Art. 155 CP', descricao: 'Furto simples' }],
    ...overrides,
  };
  return cy.apiComo('agente', 'POST', '/v1/ocorrencias', corpo).then((r) => {
    expect(r.status, 'registro da ocorrência').to.eq(201);
    return r.body as unknown as { ocorrencia_id: string; numero_protocolo: string };
  });
});

Cypress.Commands.add('limparOrdensAtivas', () => {
  cy.apiComo('operador', 'GET', '/v1/despachos?somente_ativas=true').then((r) => {
    const ordens = (r.body as Array<{ ocorrencia_id: string }>) ?? [];
    if (ordens.length === 0) return;
    cy.wrap(ordens).each((ordem) => {
      cy.apiComo('operador', 'POST', `/v1/ocorrencias/${ordem.ocorrencia_id}/encerrar`, {
        desfecho: 'Encerramento automático de limpeza E2E (ordem ativa residual)',
      }).its('status').should('eq', 200);
    });
  });
});

export {};
