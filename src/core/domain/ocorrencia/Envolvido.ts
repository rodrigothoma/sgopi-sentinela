import { ErroValidacao } from "../shared/DomainError";

export const TipoEnvolvido = {
  VITIMA: "VITIMA",
  TESTEMUNHA: "TESTEMUNHA",
  SUSPEITO: "SUSPEITO",
} as const;
export type TipoEnvolvido = (typeof TipoEnvolvido)[keyof typeof TipoEnvolvido];

export interface Envolvido {
  readonly id: string;
  readonly nome: string;
  readonly tipo: TipoEnvolvido;
  /** CPF ou outro documento — dado sensível (RNF02: nunca exposto publicamente). */
  readonly documento?: string;
  readonly dataNascimento?: string;
  readonly observacoes?: string;
}

export function validarEnvolvido(e: Envolvido): void {
  if (!e.nome || e.nome.trim().length < 3) {
    throw new ErroValidacao("Nome do envolvido deve ter ao menos 3 caracteres.", { id: e.id });
  }
  if (!Object.values(TipoEnvolvido).includes(e.tipo)) {
    throw new ErroValidacao("Tipo de envolvido inválido.", { tipo: e.tipo });
  }
}
