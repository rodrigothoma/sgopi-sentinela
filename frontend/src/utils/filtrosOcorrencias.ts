import type { FiltrosOcorrencias, OrigemOcorrencia } from '../types/api';

/** Nome de cada filtro na query string da página (link compartilhável) — o mesmo da API, exceto as datas. */
const CHAVES_URL: Record<keyof FiltrosOcorrencias, string> = {
  texto: 'texto',
  protocolo: 'protocolo',
  natureza: 'natureza',
  origem: 'origem',
  dataFatoDe: 'de',
  dataFatoAte: 'ate',
};
const ORIGENS: OrigemOcorrencia[] = ['POLICIAL', 'PUBLICA'];

export function lerFiltrosDaUrl(params: URLSearchParams): FiltrosOcorrencias {
  const filtros: FiltrosOcorrencias = {};
  (Object.keys(CHAVES_URL) as (keyof FiltrosOcorrencias)[]).forEach((chave) => {
    const valor = params.get(CHAVES_URL[chave])?.trim();
    if (valor) (filtros as Record<string, string>)[chave] = valor;
  });
  if (filtros.origem && !ORIGENS.includes(filtros.origem)) delete filtros.origem;
  return filtros;
}

/** Devolve uma cópia de ``params`` com os filtros aplicados (preserva outros parâmetros, ex.: ``ocorrencia``). */
export function escreverFiltrosNaUrl(params: URLSearchParams, filtros: FiltrosOcorrencias): URLSearchParams {
  const novos = new URLSearchParams(params);
  (Object.keys(CHAVES_URL) as (keyof FiltrosOcorrencias)[]).forEach((chave) => {
    const valor = filtros[chave]?.trim();
    if (valor) novos.set(CHAVES_URL[chave], valor);
    else novos.delete(CHAVES_URL[chave]);
  });
  return novos;
}

export function temFiltroAtivo(filtros: FiltrosOcorrencias): boolean {
  return Object.values(filtros).some((v) => typeof v === 'string' && v.trim() !== '');
}

/** Converte o dia local do ``<input type="date">`` no instante ISO (com fuso) esperado pela API. */
function inicioDoDia(dia: string): string {
  return new Date(`${dia}T00:00:00`).toISOString();
}

function fimDoDia(dia: string): string {
  return new Date(`${dia}T23:59:59.999`).toISOString();
}

/** Acrescenta os filtros de busca aos parâmetros da requisição ``GET /v1/ocorrencias``. */
export function aplicarFiltrosNaApi(params: URLSearchParams, filtros: FiltrosOcorrencias = {}): URLSearchParams {
  if (filtros.texto?.trim()) params.set('texto', filtros.texto.trim());
  if (filtros.protocolo?.trim()) params.set('protocolo', filtros.protocolo.trim());
  if (filtros.natureza?.trim()) params.set('natureza', filtros.natureza.trim());
  if (filtros.origem) params.set('origem', filtros.origem);
  if (filtros.dataFatoDe) params.set('data_fato_de', inicioDoDia(filtros.dataFatoDe));
  if (filtros.dataFatoAte) params.set('data_fato_ate', fimDoDia(filtros.dataFatoAte));
  return params;
}
