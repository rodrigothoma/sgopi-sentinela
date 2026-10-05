import { describe, expect, it } from 'vitest';
import { formatarDuracao } from '../duracao';

describe('formatarDuracao', () => {
  it('escolhe a unidade pela grandeza', () => {
    expect(formatarDuracao(null)).toBe('—');
    expect(formatarDuracao(44.6)).toBe('45 s');
    expect(formatarDuracao(720)).toBe('12 min');
    expect(formatarDuracao(4800)).toBe('1 h 20 min');
    expect(formatarDuracao(7200)).toBe('2 h');
  });
});
