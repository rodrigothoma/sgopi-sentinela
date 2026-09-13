import type { Coordenada } from "../shared/Coordenada";

/**
 * Modo do despacho (RNF04):
 *  - AUTOMATICO: proximidade calculada pelo sistema com GPS válido.
 *  - MANUAL_POSICAO_INFORMADA: GPS desatualizado; operador informou a posição
 *    via rádio (UC02 — Cenário de Exceção I).
 */
export const ModoDespacho = {
  AUTOMATICO: "AUTOMATICO",
  MANUAL_POSICAO_INFORMADA: "MANUAL_POSICAO_INFORMADA",
} as const;
export type ModoDespacho = (typeof ModoDespacho)[keyof typeof ModoDespacho];

/**
 * Registro imutável da ordem de serviço (critério de aceite 5 do MVP):
 * data/hora, operador responsável, viatura designada e identificador da ocorrência.
 */
export interface OrdemDespacho {
  readonly id: string;
  readonly ocorrenciaId: string;
  readonly protocoloOcorrencia: string;
  readonly viaturaId: string;
  readonly prefixoViatura: string;
  readonly operadorId: string;
  readonly emitidaEm: Date;
  readonly modo: ModoDespacho;
  readonly distanciaKm?: number;
  readonly posicaoInformada?: Coordenada;
  readonly observacao?: string;
}
