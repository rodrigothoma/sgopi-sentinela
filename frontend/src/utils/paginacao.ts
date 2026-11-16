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
