/**
 * Validação e máscara de documentos (CPF/RG) no cliente — espelha
 * `domain/shared/documentos.py` do backend: só dígitos, com tamanho FIXO —
 * CPF = 11 dígitos; RG = 10 dígitos (padrão RS). Os dígitos verificadores do CPF
 * não são conferidos (decisão de produto); `cpfValido` fica disponível se precisar.
 */
export type TipoDocumento = 'CPF' | 'RG';

/** Quantidade exata de dígitos aceita por tipo de documento. */
export const TAMANHO_DOCUMENTO: Record<TipoDocumento, number> = { CPF: 11, RG: 10 };

export const somenteDigitos = (v: string): string => v.replace(/\D/g, '');

/** Confere os dois dígitos verificadores; rejeita sequências repetidas (111.111.111-11). */
export function cpfValido(valor: string): boolean {
  const cpf = somenteDigitos(valor);
  if (cpf.length !== 11 || /^(\d)\1{10}$/.test(cpf)) return false;
  for (const tamanho of [9, 10]) {
    let soma = 0;
    for (let i = 0; i < tamanho; i++) soma += Number(cpf[i]) * (tamanho + 1 - i);
    let digito = (soma * 10) % 11;
    if (digito === 10) digito = 0;
    if (digito !== Number(cpf[tamanho])) return false;
  }
  return true;
}

/** Aplica a máscara 000.000.000-00 progressivamente enquanto o usuário digita. */
export function formatarCpf(valor: string): string {
  const d = somenteDigitos(valor).slice(0, 11);
  if (d.length <= 3) return d;
  if (d.length <= 6) return `${d.slice(0, 3)}.${d.slice(3)}`;
  if (d.length <= 9) return `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6)}`;
  return `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6, 9)}-${d.slice(9)}`;
}

/** Limita o valor digitado aos dígitos permitidos para o tipo (o campo nunca aceita letras). */
export function limitarDigitos(tipo: TipoDocumento, valor: string): string {
  return somenteDigitos(valor).slice(0, TAMANHO_DOCUMENTO[tipo]);
}

/** Exibição: CPF mascarado, RG só dígitos. */
export function formatarDocumento(tipo: TipoDocumento, digitos: string): string {
  return tipo === 'CPF' ? formatarCpf(digitos) : limitarDigitos('RG', digitos);
}

export type ProblemaDocumento = 'cpf_incompleto' | 'rg_tamanho' | null;

/** Valida só o tamanho (dígitos já são garantidos pelo campo); string vazia é válida (documento é opcional). */
export function validarDocumento(tipo: TipoDocumento, digitos: string): ProblemaDocumento {
  const d = somenteDigitos(digitos);
  if (!d) return null;
  if (d.length === TAMANHO_DOCUMENTO[tipo]) return null;
  return tipo === 'CPF' ? 'cpf_incompleto' : 'rg_tamanho';
}

/** Deduz o tipo de um documento já gravado (o backend trata 11 dígitos como CPF). */
export function tipoDoDocumento(valor: string | null | undefined): TipoDocumento {
  return somenteDigitos(valor ?? '').length === 11 ? 'CPF' : 'RG';
}

/** Nome do envolvido: letras (com acentos), espaços, apóstrofo e hífen — nunca dígitos. */
const NOME_PERMITIDO = /^[\p{L}\p{M}\s'\-.]+$/u;

export type ProblemaNome = 'nome_vazio' | 'nome_invalido' | null;

export function validarNome(nome: string): ProblemaNome {
  const n = nome.trim();
  if (!n) return 'nome_vazio';
  return NOME_PERMITIDO.test(n) ? null : 'nome_invalido';
}

/** Remove dígitos enquanto o usuário digita/cola no campo de nome. */
export const semDigitos = (v: string): string => v.replace(/\d/g, '');
