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

export function listarCriticas24h(
  ocorrencias: OcorrenciaResumo[],
  natureza: string,
  agora: number = Date.now(),
): OcorrenciaResumo[] {
  const corte = agora - MS_POR_DIA;
  return ocorrencias
    .filter(
      (o) =>
        (natureza === '' || o.natureza === natureza) &&
        new Date(o.data_hora_fato).getTime() >= corte,
    )
    .sort((a, b) => new Date(b.data_hora_fato).getTime() - new Date(a.data_hora_fato).getTime());
}

export function listarEmAberto(ocorrencias: OcorrenciaResumo[], natureza: string): OcorrenciaResumo[] {
  const filtradas =
    natureza === '' ? ocorrencias : ocorrencias.filter((o) => o.natureza === natureza);
  return [...filtradas].sort(
    (a, b) => new Date(a.criada_em).getTime() - new Date(b.criada_em).getTime(),
  );
}

export interface ResumoNatureza {
  natureza: string;
  quantidade: number;
}

export function resumirPorNatureza(ocorrencias: OcorrenciaResumo[]): ResumoNatureza[] {
  const contagem = new Map<string, number>();
  for (const o of ocorrencias) contagem.set(o.natureza, (contagem.get(o.natureza) ?? 0) + 1);
  return [...contagem.entries()]
    .map(([natureza, quantidade]) => ({ natureza, quantidade }))
    .sort((a, b) => b.quantidade - a.quantidade);
}

export function idadeEmMinutos(criadaEm: string, agora: number = Date.now()): number {
  return Math.max(0, Math.floor((agora - new Date(criadaEm).getTime()) / 60_000));
}
