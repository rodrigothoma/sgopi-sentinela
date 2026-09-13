import type { ViaturaComSinal, ResultadoSugestao } from "@/core/application/ports/inbound/CasosDeUso";
import type { EstadoOcorrencia } from "@/core/domain/ocorrencia/Ocorrencia";
import type { Serializado } from "@app/_lib/formatos";

export type ViaturaUI = Serializado<ViaturaComSinal>;
export type OcorrenciaUI = Serializado<EstadoOcorrencia>;
export type SugestaoUI = Serializado<ResultadoSugestao>;

/** Mesma tolerância do domínio (UC02 RN3), recalculada no cliente entre eventos. */
export const TOLERANCIA_GPS_MS = 60_000;

export function recalcularSinal(v: ViaturaUI, agora = Date.now()): ViaturaUI {
  const valido = !!v.ultimaPosicao && agora - new Date(v.ultimaPosicao.recebidaEm).getTime() <= TOLERANCIA_GPS_MS;
  return v.sinalGpsValido === valido ? v : { ...v, sinalGpsValido: valido };
}
