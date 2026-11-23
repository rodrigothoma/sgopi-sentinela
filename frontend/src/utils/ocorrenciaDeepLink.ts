import type { StatusOcorrencia } from '../types/api';

const CHAVE_OCORRENCIA_LEGADA = 'ocorrencia';
const CHAVE_ABA = 'aba';
const ABA_PADRAO = 0;

export const GRUPOS_FILA_DELEGADO: readonly (readonly StatusOcorrencia[])[] = [
  ['AGUARDANDO_REVISAO'],
  ['EM_CORRECAO'],
  ['VALIDADA', 'EM_ATENDIMENTO'],
  ['REJEITADA', 'ENCERRADA'],
  ['ARQUIVADA', 'EXCLUIDA'],
];

export const abaDoStatus = (
  status: StatusOcorrencia,
  grupos: readonly (readonly StatusOcorrencia[])[] = GRUPOS_FILA_DELEGADO,
): number => {
  const indice = grupos.findIndex((grupo) => grupo.includes(status));
  return indice >= 0 ? indice : ABA_PADRAO;
};

export const lerAba = (params: URLSearchParams, totalAbas: number): number => {
  const bruto = params.get(CHAVE_ABA);
  if (bruto === null) return ABA_PADRAO;
  const indice = Number(bruto);
  return Number.isInteger(indice) && indice >= ABA_PADRAO && indice < totalAbas ? indice : ABA_PADRAO;
};

export const idOcorrenciaLegada = (params: URLSearchParams): string | null => {
  const id = params.get(CHAVE_OCORRENCIA_LEGADA)?.trim();
  return id || null;
};

const semParametroLegado = (params: URLSearchParams): URLSearchParams => {
  const copia = new URLSearchParams(params);
  copia.delete(CHAVE_OCORRENCIA_LEGADA);
  return copia;
};

const comQuery = (caminho: string, params: URLSearchParams): string => {
  const query = params.toString();
  return query ? `${caminho}?${query}` : caminho;
};

export const urlDoDetalhe = (
  base: '/fila' | '/minhas',
  ocorrenciaId: string,
  params: URLSearchParams,
): string => comQuery(`${base}/${encodeURIComponent(ocorrenciaId)}`, semParametroLegado(params));

export const urlDaLista = (
  base: '/fila' | '/minhas',
  params: URLSearchParams,
  aba?: number,
): string => {
  const copia = semParametroLegado(params);
  copia.delete(CHAVE_ABA);
  if (aba !== undefined) copia.set(CHAVE_ABA, String(aba));
  return comQuery(base, copia);
};
