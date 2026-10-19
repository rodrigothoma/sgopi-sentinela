import { describe, expect, it } from 'vitest';
import { formatarDuracao, formatarEspera } from '../duracao';

describe('formatarDuracao', () => {
  it('escolhe a unidade pela grandeza', () => {
    expect(formatarDuracao(null)).toBe('—');
    expect(formatarDuracao(44.6)).toBe('45 s');
    expect(formatarDuracao(720)).toBe('12 min');
    expect(formatarDuracao(4800)).toBe('1 h 20 min');
    expect(formatarDuracao(7200)).toBe('2 h');
  });
});

describe('formatarEspera', () => {
  it('abaixo de 1 h se comporta como formatarDuracao', () => {
    expect(formatarEspera(45)).toBe('45 s');
    expect(formatarEspera(720)).toBe('12 min');
  });

  it('entre 1 h e 24 h mostra horas e minutos', () => {
    expect(formatarEspera(4800)).toBe('1 h 20 min');
    expect(formatarEspera(7200)).toBe('2 h');
    expect(formatarEspera(84_600)).toBe('23 h 30 min');
  });

  it('a partir de 24 h passa a contar em dias', () => {
    expect(formatarEspera(86_400)).toBe('1 d');
    expect(formatarEspera(108_000)).toBe('1 d 6 h');
    expect(formatarEspera(187_200)).toBe('2 d 4 h');
    expect(formatarEspera(259_200)).toBe('3 d');
  });

  it('propaga o arredondamento em vez de gerar 60 min ou 24 h', () => {
    // 23 h 59 min 59 s: viraria "23 h 60 min" se delegasse a formatarDuracao
    expect(formatarEspera(86_399)).toBe('1 d');
    expect(formatarEspera(3_599)).toBe('1 h');
  });
});
