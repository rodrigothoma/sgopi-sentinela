import type { Papel } from "./Papel";

export interface Usuario {
  readonly id: string;
  readonly nome: string;
  readonly matricula: string;
  readonly papel: Papel;
  /** Hash da senha (o algoritmo é responsabilidade do adaptador via `PortaHash`). */
  readonly senhaHash: string;
  readonly unidade: string;
}
