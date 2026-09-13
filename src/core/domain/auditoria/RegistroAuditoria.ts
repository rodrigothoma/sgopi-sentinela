/**
 * RNF03 — log inalterável. Cada registro carrega o hash do anterior formando
 * uma cadeia (hash chain): adulterar qualquer entrada invalida todas as
 * posteriores. O cálculo do hash é feito pelo adaptador via `PortaHash`;
 * o domínio só define a estrutura e a regra de encadeamento.
 */
export interface RegistroAuditoria {
  readonly sequencia: number;
  readonly registradoEm: Date;
  readonly atorId: string;
  readonly atorPapel: string;
  readonly acao: string;
  readonly recursoTipo: string;
  readonly recursoId: string;
  readonly resultado: "SUCESSO" | "NEGADO" | "ERRO";
  readonly detalhes?: Record<string, unknown>;
  readonly hashAnterior: string;
  readonly hash: string;
}

export type NovoRegistroAuditoria = Omit<RegistroAuditoria, "sequencia" | "registradoEm" | "hashAnterior" | "hash">;

/** Serialização canônica usada para calcular o hash (determinística). */
export function conteudoCanonico(r: Omit<RegistroAuditoria, "hash">): string {
  return JSON.stringify({
    sequencia: r.sequencia,
    registradoEm: r.registradoEm.toISOString(),
    atorId: r.atorId,
    atorPapel: r.atorPapel,
    acao: r.acao,
    recursoTipo: r.recursoTipo,
    recursoId: r.recursoId,
    resultado: r.resultado,
    detalhes: r.detalhes ?? null,
    hashAnterior: r.hashAnterior,
  });
}
