import { describe, expect, it } from 'vitest';
import { normalizarDigitos, validarCpf } from '../cpf';

describe('validarCpf', () => {
  it('aceita CPF com dígitos verificadores corretos, com ou sem máscara', () => {
    expect(validarCpf('529.982.247-25')).toBe(true);
    expect(validarCpf('52998224725')).toBe(true);
  });

  it('recusa sequência repetida, tamanho errado e dígito incorreto', () => {
    expect(validarCpf('111.111.111-11')).toBe(false);
    expect(validarCpf('123')).toBe(false);
    expect(validarCpf('529.982.247-24')).toBe(false);
  });

  it('normaliza dígitos', () => {
    expect(normalizarDigitos('(55) 99876-5432')).toBe('55998765432');
  });
});
