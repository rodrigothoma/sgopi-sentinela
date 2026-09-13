import type { EventoDominio } from "@/core/domain/shared/Evento";
import type { StatusOcorrencia } from "@/core/domain/ocorrencia/StatusOcorrencia";
import type { Coordenada } from "@/core/domain/shared/Coordenada";
import type { StatusViatura } from "@/core/domain/viatura/Viatura";

export type EventoOcorrenciaAlterada = EventoDominio<
  "ocorrencia.alterada",
  { ocorrenciaId: string; protocolo: string; status: StatusOcorrencia; gravidade: number; coordenada?: Coordenada }
>;

export type EventoViaturaPosicao = EventoDominio<
  "viatura.posicao",
  { viaturaId: string; prefixo: string; status: StatusViatura; coordenada: Coordenada; recebidaEm: string }
>;

export type EventoViaturaDespachada = EventoDominio<
  "viatura.despachada",
  { viaturaId: string; prefixo: string; ocorrenciaId: string; protocolo: string; ordemId: string }
>;

export type EventoSgopi = EventoOcorrenciaAlterada | EventoViaturaPosicao | EventoViaturaDespachada;
