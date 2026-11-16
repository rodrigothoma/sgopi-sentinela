/** Cálculos de paginação no servidor (páginas contadas a partir de 1). */

export function totalDePaginas(total: number, porPagina: number): number {
  return Math.max(1, Math.ceil(total / porPagina));
}

export function offsetDaPagina(pagina: number, porPagina: number): number {
  return (pagina - 1) * porPagina;
}

/** Posição (1-based) do primeiro e do último item exibidos; ``{0, 0}`` quando não há itens. */
export function faixaDaPagina(pagina: number, porPagina: number, total: number): { inicio: number; fim: number } {
  if (total === 0) return { inicio: 0, fim: 0 };
  const inicio = offsetDaPagina(pagina, porPagina) + 1;
  return { inicio, fim: Math.min(total, inicio + porPagina - 1) };
}

export const RETICENCIAS = '…';
/** Até este total, todas as páginas aparecem; acima, entram as reticências. */
const MAXIMO_SEM_RETICENCIAS = 7;
const VIZINHAS = 1;

/** Números a exibir na navegação: primeira, última e vizinhas da atual, com "…" nos saltos. */
export function paginasVisiveis(atual: number, total: number): (number | typeof RETICENCIAS)[] {
  if (total <= MAXIMO_SEM_RETICENCIAS) return Array.from({ length: total }, (_, i) => i + 1);
  const paginas = new Set([1, total]);
  for (let p = atual - VIZINHAS; p <= atual + VIZINHAS; p += 1) {
    if (p >= 1 && p <= total) paginas.add(p);
  }
  const ordenadas = [...paginas].sort((a, b) => a - b);
  const resultado: (number | typeof RETICENCIAS)[] = [];
  ordenadas.forEach((p, i) => {
    const anterior = ordenadas[i - 1];
    if (anterior !== undefined && p - anterior === 2) resultado.push(anterior + 1); // não esconder uma página só
    else if (anterior !== undefined && p - anterior > 2) resultado.push(RETICENCIAS);
    resultado.push(p);
  });
  return resultado;
}

/** Página digitada em "Ir para", limitada ao intervalo; ``null`` se não for um número. */
export function paginaValida(texto: string, total: number): number | null {
  const numero = Number.parseInt(texto, 10);
  if (Number.isNaN(numero)) return null;
  return Math.min(Math.max(numero, 1), total);
}
