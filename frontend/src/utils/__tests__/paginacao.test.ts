import { describe, expect, it } from 'vitest';
import { faixaDaPagina, offsetDaPagina, paginaValida, paginasVisiveis, totalDePaginas } from '../paginacao';

describe('totalDePaginas', () => {
  it('arredonda para cima e nunca é menor que 1', () => {
    expect(totalDePaginas(237, 50)).toBe(5);
    expect(totalDePaginas(250, 50)).toBe(5);
    expect(totalDePaginas(0, 50)).toBe(1);
  });
});

describe('offsetDaPagina', () => {
  it('converte página (a partir de 1) em deslocamento', () => {
    expect(offsetDaPagina(1, 50)).toBe(0);
    expect(offsetDaPagina(3, 50)).toBe(100);
  });
});

describe('faixaDaPagina', () => {
  it('mostra a posição dos itens exibidos no total', () => {
    expect(faixaDaPagina(1, 50, 237)).toEqual({ inicio: 1, fim: 50 });
    expect(faixaDaPagina(5, 50, 237)).toEqual({ inicio: 201, fim: 237 });
  });

  it('sem itens a faixa é zerada', () => {
    expect(faixaDaPagina(1, 50, 0)).toEqual({ inicio: 0, fim: 0 });
  });
});

describe('paginasVisiveis', () => {
  it('com poucas páginas mostra todas', () => {
    expect(paginasVisiveis(1, 5)).toEqual([1, 2, 3, 4, 5]);
    expect(paginasVisiveis(1, 1)).toEqual([1]);
  });

  it('no meio mostra a primeira, a última e as vizinhas da atual, com reticências', () => {
    expect(paginasVisiveis(10, 20)).toEqual([1, '…', 9, 10, 11, '…', 20]);
  });

  it('perto das pontas não deixa reticência que esconderia uma página só', () => {
    expect(paginasVisiveis(1, 20)).toEqual([1, 2, '…', 20]);
    expect(paginasVisiveis(3, 20)).toEqual([1, 2, 3, 4, '…', 20]);
    expect(paginasVisiveis(4, 20)).toEqual([1, 2, 3, 4, 5, '…', 20]);
    expect(paginasVisiveis(18, 20)).toEqual([1, '…', 17, 18, 19, 20]);
  });
});

describe('paginaValida', () => {
  it('limita ao intervalo de páginas e ignora o que não é número', () => {
    expect(paginaValida('3', 5)).toBe(3);
    expect(paginaValida('0', 5)).toBe(1);
    expect(paginaValida('99', 5)).toBe(5);
    expect(paginaValida('abc', 5)).toBeNull();
    expect(paginaValida('', 5)).toBeNull();
  });
});
