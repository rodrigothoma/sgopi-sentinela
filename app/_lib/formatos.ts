export function dataHora(v: string | Date | undefined): string {
  if (!v) return "—";
  return new Date(v).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "medium" });
}

export const ROTULO_GRAVIDADE: Record<number, string> = { 1: "Baixa", 2: "Média", 3: "Alta", 4: "Crítica" };

/** Converte Dates em strings para atravessar a fronteira servidor → cliente. */
export function serializar<T>(v: T): Serializado<T> {
  return JSON.parse(JSON.stringify(v)) as Serializado<T>;
}

export type Serializado<T> = T extends Date
  ? string
  : T extends readonly (infer U)[]
    ? Serializado<U>[]
    : T extends object
      ? { [K in keyof T]: Serializado<T[K]> }
      : T;
