import { describe, expect, it } from 'vitest';
import { codigoValido, formatarChave, normalizarCodigo } from '../autenticidade';

describe('chave de autenticidade (RF08)', () => {
  it('formata em grupos de 4 e normaliza o que vem colado de um PDF', () => {
    expect(formatarChave('abcd efgh-jkmn\npqrs')).toBe('ABCD-EFGH-JKMN-PQRS');
    expect(normalizarCodigo(' ab-cd ')).toBe('abcd');
  });

  it('aceita chave de 24 caracteres ou hash SHA-256 hexadecimal', () => {
    expect(codigoValido('A'.repeat(24))).toBe(true);
    expect(codigoValido('f'.repeat(64))).toBe(true);
    expect(codigoValido('g'.repeat(64))).toBe(false);
    expect(codigoValido('A'.repeat(23))).toBe(false);
  });
});
