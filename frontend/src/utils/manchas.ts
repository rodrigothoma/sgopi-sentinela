import type { OcorrenciaResumo } from '../types/api';

export type PontoCalor = [number, number, number];

export const PERIODO_MANCHA_PADRAO_DIAS = 7;
export const PERIODOS_MANCHA_DIAS = [7, 30] as const;
export const LIMIAR_CRITICIDADE_24H = 3;

const MS_POR_DIA = 86_400_000;

export function listarNaturezas(ocorrencias: OcorrenciaResumo[]): string[] {
  return [...new Set(ocorrencias.map((o) => o.natureza))].sort((a, b) => a.localeCompare(b));
}

export function filtrarPontosMancha(
  ocorrencias: OcorrenciaResumo[],
  periodoDias: number,
  natureza: string,
  agora: number = Date.now(),
): PontoCalor[] {
  const corte = agora - periodoDias * MS_POR_DIA;
  return ocorrencias
    .filter(
      (o) =>
        (natureza === '' || o.natureza === natureza) &&
        new Date(o.data_hora_fato).getTime() >= corte,
    )
    .map((o) => [o.latitude, o.longitude, 1]);
}

export function contarOcorrencias24h(
  ocorrencias: OcorrenciaResumo[],
  natureza: string,
  agora: number = Date.now(),
): number {
  const corte = agora - MS_POR_DIA;
  return ocorrencias.filter(
    (o) =>
      (natureza === '' || o.natureza === natureza) &&
      new Date(o.data_hora_fato).getTime() >= corte,
  ).length;
}
