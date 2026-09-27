/**
 * Chave pública de autenticidade do documento (RF08) — espelha
 * `domain/ocorrencia/autenticidade.py`: 24 caracteres sem 0/O/1/I, exibida em
 * grupos de 4; o QR Code aponta para a página pública /autenticar/<chave>.
 */
export const TAMANHO_CHAVE = 24;
export const TAMANHO_HASH = 64;
const TAMANHO_GRUPO = 4;

/** Remove tudo que não é letra/dígito (hífens, espaços, quebras de linha coladas de um PDF). */
export const normalizarCodigo = (valor: string): string => valor.replace(/[^A-Za-z0-9]/g, '');

/** XXXX-XXXX-XXXX-XXXX-XXXX-XXXX */
export const formatarChave = (chave: string): string =>
  normalizarCodigo(chave).toUpperCase().match(new RegExp(`.{1,${TAMANHO_GRUPO}}`, 'g'))?.join('-') ?? '';

/** Formato aceito pelo backend: chave completa ou hash SHA-256 completo. */
export const codigoValido = (valor: string): boolean => {
  const limpo = normalizarCodigo(valor);
  return limpo.length === TAMANHO_CHAVE || (limpo.length === TAMANHO_HASH && /^[0-9a-fA-F]+$/.test(limpo));
};

/** URL absoluta codificada no QR Code impresso no comprovante. */
export const urlAutenticacao = (chave: string): string => `${window.location.origin}/autenticar/${normalizarCodigo(chave).toUpperCase()}`;
