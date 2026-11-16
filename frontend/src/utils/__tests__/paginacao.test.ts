import { describe, expect, it } from 'vitest';
import { faixaDaPagina, offsetDaPagina, totalDePaginas } from '../paginacao';

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
