import type { OcorrenciaResumo } from '../types/api';

/** Abaixo disso a busca não dispara: evita varrer a base a cada tecla. */
export const MINIMO_CARACTERES_BUSCA = 2;
export const MAXIMO_RESULTADOS_BUSCA = 6;

/** Teto de palavras por busca: cada termo custa uma consulta por campo. */
export const MAXIMO_TERMOS_BUSCA = 4;

/**
 * Quantos candidatos cada campo devolve quando há mais de um termo.
 *
 * Com um termo só bastam os ``MAXIMO_RESULTADOS_BUSCA`` exibidos. Com vários, o
 * cruzamento é feito no cliente: pedir só 6 por campo esconderia a ocorrência
 * que casa com todos os termos mas não está entre as 6 primeiras de nenhum.
 */
export const MAXIMO_CANDIDATOS_TERMO = 25;

export function termoBuscavel(termo: string): boolean {
  return termo.trim().length >= MINIMO_CARACTERES_BUSCA;
}

/** Quebra a entrada em palavras; cada uma vira uma rodada de consultas. */
export function separarTermos(entrada: string): string[] {
  const palavras = entrada.trim().split(/\s+/).filter(Boolean);
  return palavras.slice(0, MAXIMO_TERMOS_BUSCA);
}

/**
 * Une os resultados das consultas por protocolo, natureza e endereço.
 *
 * Os filtros da API combinam com E, então a busca livre precisa de uma consulta
 * por campo; aqui elas viram uma lista só. A ordem das listas é a prioridade de
 * exibição — quem procura "000012" espera o protocolo no topo.
 */
export function mesclarResultadosBusca(
  listas: OcorrenciaResumo[][],
  maximo: number = MAXIMO_RESULTADOS_BUSCA,
): OcorrenciaResumo[] {
  const vistos = new Set<string>();
  const mesclado: OcorrenciaResumo[] = [];

  for (const lista of listas) {
    for (const ocorrencia of lista) {
      if (vistos.has(ocorrencia.ocorrencia_id)) continue;
      vistos.add(ocorrencia.ocorrencia_id);
      mesclado.push(ocorrencia);
      if (mesclado.length === maximo) return mesclado;
    }
  }
  return mesclado;
}

/**
 * Cruza os achados de cada termo: só sobrevive quem casou com todos.
 *
 * Quem digita "roubo andradas" espera restringir, não somar — cada palavra a
 * mais estreita o resultado. A ordem é a do primeiro termo, que é o mais
 * específico na prática: é por ele que a pessoa começou a digitar.
 */
export function intersectarResultados(
  listas: OcorrenciaResumo[][],
  maximo: number = MAXIMO_RESULTADOS_BUSCA,
): OcorrenciaResumo[] {
  const [primeira, ...demais] = listas;
  if (!primeira) return [];

  const idsPorTermo = demais.map((lista) => new Set(lista.map((o) => o.ocorrencia_id)));
  const vistos = new Set<string>();
  const comuns: OcorrenciaResumo[] = [];

  for (const ocorrencia of primeira) {
    if (vistos.has(ocorrencia.ocorrencia_id)) continue;
    if (!idsPorTermo.every((ids) => ids.has(ocorrencia.ocorrencia_id))) continue;
    vistos.add(ocorrencia.ocorrencia_id);
    comuns.push(ocorrencia);
    if (comuns.length === maximo) break;
  }
  return comuns;
}
