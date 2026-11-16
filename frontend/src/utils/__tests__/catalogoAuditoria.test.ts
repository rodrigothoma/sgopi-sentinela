import { describe, expect, it } from 'vitest';
import { entidadesDoCatalogo, opcoesDoCatalogo } from '../catalogoAuditoria';

const CATALOGO = [
  { operacao: 'ocorrencia.validar', entidade: 'Ocorrencia' },
  { operacao: 'auth.login', entidade: 'Usuario' },
  { operacao: 'ocorrencia.registrar', entidade: 'Ocorrencia' },
  { operacao: 'laudo.solicitar', entidade: 'laudo_pericial' },
];

const rotulos: Record<string, string> = {
  'ocorrencia.validar': 'Ocorrência validada',
  'auth.login': 'Login realizado',
  'ocorrencia.registrar': 'Ocorrência registrada',
};
const rotular = (op: string) => rotulos[op] ?? op;

describe('opcoesDoCatalogo', () => {
  it('começa com a opção "todas" e ordena as ações pelo rótulo traduzido', () => {
    expect(opcoesDoCatalogo(CATALOGO, rotular, 'Todas')).toEqual([
      { value: 'TODAS', label: 'Todas' },
      { value: 'laudo.solicitar', label: 'laudo.solicitar' },
      { value: 'auth.login', label: 'Login realizado' },
      { value: 'ocorrencia.registrar', label: 'Ocorrência registrada' },
      { value: 'ocorrencia.validar', label: 'Ocorrência validada' },
    ]);
  });

  it('sem catálogo fica só a opção "todas"', () => {
    expect(opcoesDoCatalogo([], rotular, 'Todas')).toEqual([{ value: 'TODAS', label: 'Todas' }]);
  });
});

describe('entidadesDoCatalogo', () => {
  it('lista cada entidade uma vez, em ordem alfabética', () => {
    expect(entidadesDoCatalogo(CATALOGO)).toEqual(['laudo_pericial', 'Ocorrencia', 'Usuario']);
  });
});
