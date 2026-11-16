import type { AcaoAuditada } from '../types/api';

export const OPCAO_TODAS = 'TODAS';

export interface OpcaoFiltro {
  value: string;
  label: string;
}

const porTexto = (a: string, b: string) => a.localeCompare(b, undefined, { sensitivity: 'base' });

/** Opções do filtro de operação: "todas" primeiro e as ações do catálogo pelo rótulo traduzido. */
export function opcoesDoCatalogo(
  catalogo: AcaoAuditada[],
  rotular: (operacao: string) => string,
  rotuloTodas: string,
): OpcaoFiltro[] {
  const acoes = catalogo
    .map(({ operacao }) => ({ value: operacao, label: rotular(operacao) }))
    .sort((a, b) => porTexto(a.label, b.label));
  return [{ value: OPCAO_TODAS, label: rotuloTodas }, ...acoes];
}

/** Entidades que aparecem no catálogo, sem repetição, em ordem alfabética. */
export function entidadesDoCatalogo(catalogo: AcaoAuditada[]): string[] {
  return Array.from(new Set(catalogo.map((a) => a.entidade))).sort(porTexto);
}
