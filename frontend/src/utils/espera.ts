import type { StatusOcorrencia } from '../types/api';
import { formatarEspera } from './duracao';

/** Horas de espera a partir das quais a triagem passa a ser sinalizada. */
export const ESPERA_ATENCAO_HORAS = 4;
export const ESPERA_CRITICA_HORAS = 24;

const MS_POR_HORA = 3_600_000;

/** Só faz sentido contar espera enquanto a ocorrência depende de uma decisão. */
export const STATUS_EM_ESPERA: readonly StatusOcorrencia[] = ['AGUARDANDO_REVISAO', 'EM_CORRECAO'];

export type NivelEspera = 'normal' | 'atencao' | 'critico';

export interface Espera {
  nivel: NivelEspera;
  horas: number;
  /** Tempo decorrido já formatado ("6 h", "2 d 4 h"). */
  texto: string;
}

/**
 * Há quanto tempo a ocorrência aguarda decisão, e com que urgência.
 *
 * Devolve ``null`` quando não há espera a mostrar — status que não depende de
 * decisão ou data de criação inválida —, para que o chamador simplesmente não
 * renderize o selo.
 */
export function calcularEspera(
  criadaEm: string,
  status: StatusOcorrencia,
  agora: number = Date.now(),
): Espera | null {
  if (!STATUS_EM_ESPERA.includes(status)) return null;

  const inicio = new Date(criadaEm).getTime();
  if (Number.isNaN(inicio)) return null;

  const decorridoMs = Math.max(0, agora - inicio);
  const horas = decorridoMs / MS_POR_HORA;

  const nivel: NivelEspera =
    horas >= ESPERA_CRITICA_HORAS ? 'critico' : horas >= ESPERA_ATENCAO_HORAS ? 'atencao' : 'normal';

  return { nivel, horas, texto: formatarEspera(Math.round(decorridoMs / 1000)) };
}
