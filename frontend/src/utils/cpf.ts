/**
 * Utilitários de validação e máscara para CPF, telefone e e-mail.
 */

export function normalizarDigitos(valor: string): string {
  return valor.replace(/\D/g, '');
}

/**
 * Validação dos dois dígitos verificadores do CPF (módulo 11).
 * Rejeita sequências de dígitos repetidos (ex: 111.111.111-11).
 */
export function validarCpf(valor: string): boolean {
  const cpf = normalizarDigitos(valor);
  if (cpf.length !== 11 || /^(\d)\1{10}$/.test(cpf)) {
    return false;
  }

  for (const tamanho of [9, 10]) {
    let soma = 0;
    for (let i = 0; i < tamanho; i++) {
      soma += parseInt(cpf[i], 10) * (tamanho + 1 - i);
    }
    let digito = (soma * 10) % 11;
    if (digito === 10) digito = 0;
    if (digito !== parseInt(cpf[tamanho], 10)) {
      return false;
    }
  }

  return true;
}

/**
 * Aplica máscara progressiva de CPF: 000.000.000-00
 */
export function mascararCpfInput(valor: string): string {
  const d = normalizarDigitos(valor).slice(0, 11);
  if (d.length <= 3) return d;
  if (d.length <= 6) return `${d.slice(0, 3)}.${d.slice(3)}`;
  if (d.length <= 9) return `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6)}`;
  return `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6, 9)}-${d.slice(9, 11)}`;
}

/**
 * Aplica máscara de telefone: (00) 00000-0000 ou (00) 0000-0000
 */
export function mascararTelefoneInput(valor: string): string {
  const d = normalizarDigitos(valor).slice(0, 11);
  if (d.length <= 2) return d ? `(${d}` : '';
  if (d.length <= 6) return `(${d.slice(0, 2)}) ${d.slice(2)}`;
  if (d.length <= 10) return `(${d.slice(0, 2)}) ${d.slice(2, 6)}-${d.slice(6)}`;
  return `(${d.slice(0, 2)}) ${d.slice(2, 7)}-${d.slice(7, 11)}`;
}

/**
 * Validação de formato de e-mail.
 */
export function validarEmail(email: string): boolean {
  const limpo = email.trim();
  if (!limpo || limpo.length > 255) return false;
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(limpo);
}
