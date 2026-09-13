import type { Papel } from "@/core/domain/usuario/Papel";

/** Identidade autenticada que invoca um caso de uso. */
export interface Ator {
  readonly id: string;
  readonly nome: string;
  readonly papel: Papel;
}

/** Ator técnico para rotinas automáticas (simulador GPS, jobs). */
export const ATOR_SISTEMA: Ator = Object.freeze({ id: "sistema", nome: "Sistema", papel: "SUPERVISOR" });
