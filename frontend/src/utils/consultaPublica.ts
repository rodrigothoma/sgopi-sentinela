/**
 * Detecção do tipo de código informado na consulta pública.
 *
 * O portal aceita, num único campo, dois identificadores de natureza distinta:
 * - protocolo `SGOPI-AAAA-NNNNNN` (acompanhamento da ocorrência, gerado no registro);
 * - chave de autenticidade de 24 caracteres (RF08, gerada na validação pelo Delegado).
 *
 * O alfabeto e o tamanho espelham `domain/ocorrencia/autenticidade.py`.
 */
export type ModoConsulta = 'protocolo' | 'chave';

const PREFIXO_PROTOCOLO = 'SGOPI';
const PADRAO_PROTOCOLO = /^SGOPI-\d{4}-\d{6}$/;
const ALFABETO_CHAVE = /^[ABCDEFGHJKLMNPQRSTUVWXYZ23456789]+$/;
const TAMANHO_CHAVE = 24;
const TAMANHO_GRUPO = 4;

export const PLACEHOLDER: Record<ModoConsulta, string> = {
  protocolo: 'SGOPI-AAAA-NNNNNN',
  chave: 'XXXX-XXXX-XXXX-XXXX-XXXX-XXXX',
};

/** Remove tudo que não é letra/dígito e coloca em maiúsculas. */
export function normalizarChave(valor: string): string {
  return valor.toUpperCase().replace(/[^A-Z0-9]/g, '');
}

export function ehProtocolo(valor: string): boolean {
  return PADRAO_PROTOCOLO.test(valor.trim().toUpperCase());
}

export function ehChave(valor: string): boolean {
  const chave = normalizarChave(valor);
  return chave.length === TAMANHO_CHAVE && ALFABETO_CHAVE.test(chave);
}

/**
 * Infere o modo a partir do que o usuário digitou. Devolve `null` quando ainda
 * não dá para saber (campo vazio ou formato incompleto) — nesse caso o modo
 * escolhido manualmente é mantido.
 */
export function detectarModoConsulta(valor: string): ModoConsulta | null {
  const limpo = valor.trim().toUpperCase();
  if (!limpo) return null;
  if (limpo.startsWith(PREFIXO_PROTOCOLO)) return 'protocolo';
  if (ehChave(limpo)) return 'chave';
  return null;
}

export interface EntradaConsulta {
  modo: ModoConsulta;
  valor: string;
}

/**
 * Lê o código vindo da URL, em ordem de precedência: deep-link do QR Code
 * (`/autenticar/:chave`), `?chave=`, `?protocolo=` e `?codigo=` (detecta o modo).
 * Devolve `null` quando a página foi aberta sem código.
 */
export function lerEntradaDaUrl(chaveDaRota: string | undefined, params: URLSearchParams): EntradaConsulta | null {
  const chave = chaveDaRota ?? params.get('chave');
  if (chave) return { modo: 'chave', valor: formatarChave(chave) };

  const protocolo = params.get('protocolo');
  if (protocolo) return { modo: 'protocolo', valor: protocolo.trim().toUpperCase() };

  const codigo = params.get('codigo');
  if (!codigo) return null;
  const modo = detectarModoConsulta(codigo) ?? 'protocolo';
  return { modo, valor: modo === 'chave' ? formatarChave(codigo) : codigo.trim().toUpperCase() };
}

/** `XXXX-XXXX-…` — forma legível da chave, igual à impressa no documento. */
export function formatarChave(chave: string): string {
  const limpa = normalizarChave(chave);
  const grupos: string[] = [];
  for (let i = 0; i < limpa.length; i += TAMANHO_GRUPO) {
    grupos.push(limpa.slice(i, i + TAMANHO_GRUPO));
  }
  return grupos.join('-');
}
