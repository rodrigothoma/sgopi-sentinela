import type { Papel } from "@/core/domain/usuario/Papel";

export interface ItemMenu { href: string; rotulo: string; papeis: readonly Papel[] }

export const MENU: readonly ItemMenu[] = [
  { href: "/ocorrencias", rotulo: "Ocorrências", papeis: ["AGENTE", "DELEGADO", "OPERADOR_CENTRAL", "SUPERVISOR", "PERITO"] },
  { href: "/ocorrencias/nova", rotulo: "Nova ocorrência", papeis: ["AGENTE"] },
  { href: "/revisao", rotulo: "Fila de revisão", papeis: ["DELEGADO"] },
  { href: "/painel-tatico", rotulo: "Painel tático", papeis: ["OPERADOR_CENTRAL", "SUPERVISOR", "DELEGADO"] },
  { href: "/auditoria", rotulo: "Auditoria", papeis: ["SUPERVISOR", "DELEGADO"] },
];

export function rotaInicialPorPapel(papel: Papel): string {
  switch (papel) {
    case "DELEGADO": return "/revisao";
    case "OPERADOR_CENTRAL": return "/painel-tatico";
    case "SUPERVISOR": return "/painel-tatico";
    default: return "/ocorrencias";
  }
}

export const ROTULO_PAPEL: Record<Papel, string> = {
  AGENTE: "Agente Policial",
  DELEGADO: "Delegado(a)",
  PERITO: "Perito(a)",
  OPERADOR_CENTRAL: "Operador(a) de Central",
  SUPERVISOR: "Supervisor(a)",
  CIDADAO: "Cidadão",
};
