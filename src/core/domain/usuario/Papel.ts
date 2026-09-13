/** Papéis do RBAC (RNF02). */
export const Papel = {
  AGENTE: "AGENTE",
  DELEGADO: "DELEGADO",
  PERITO: "PERITO",
  OPERADOR_CENTRAL: "OPERADOR_CENTRAL",
  SUPERVISOR: "SUPERVISOR",
  CIDADAO: "CIDADAO",
} as const;

export type Papel = (typeof Papel)[keyof typeof Papel];

export const TODOS_OS_PAPEIS: readonly Papel[] = Object.values(Papel);

export function ehPapel(valor: unknown): valor is Papel {
  return typeof valor === "string" && (TODOS_OS_PAPEIS as readonly string[]).includes(valor);
}
