import type { Usuario } from "@/core/domain/usuario/Usuario";
import type { EstadoViatura } from "@/core/domain/viatura/Viatura";
import type { PortaHash } from "@/core/application/ports/outbound/Infraestrutura";

/** Centro de referência do simulador: Alegrete/RS (sede da Unipampa). */
export const CENTRO_ALEGRETE = { latitude: -29.7831, longitude: -55.7918 } as const;

/**
 * Usuários de demonstração. Senha de todos: `sgopi123`.
 * Em produção, o cadastro vem de um adaptador de identidade (LDAP/OIDC).
 */
export function usuariosSeed(hash: PortaHash): Usuario[] {
  const senhaHash = hash.sha256("sgopi123");
  return [
    { id: "u-agente-1", nome: "Ag. Carla Menezes", matricula: "agente", papel: "AGENTE", senhaHash, unidade: "1ª DP Alegrete" },
    { id: "u-agente-2", nome: "Ag. João Pires", matricula: "agente2", papel: "AGENTE", senhaHash, unidade: "1ª DP Alegrete" },
    { id: "u-delegado-1", nome: "Dr. Rafael Souto", matricula: "delegado", papel: "DELEGADO", senhaHash, unidade: "1ª DP Alegrete" },
    { id: "u-operador-1", nome: "Op. Luana Ferraz", matricula: "operador", papel: "OPERADOR_CENTRAL", senhaHash, unidade: "Central 190" },
    { id: "u-supervisor-1", nome: "Sup. Marcos Lima", matricula: "supervisor", papel: "SUPERVISOR", senhaHash, unidade: "Comando Regional" },
    { id: "u-perito-1", nome: "Perito Ana Kraus", matricula: "perito", papel: "PERITO", senhaHash, unidade: "IGP" },
  ];
}

export function viaturasSeed(): EstadoViatura[] {
  return [
    { id: "vtr-01", prefixo: "VTR-1201", placa: "IVX-1A20", equipe: "Alfa-1", status: "DISPONIVEL" },
    { id: "vtr-02", prefixo: "VTR-1202", placa: "IVX-2B31", equipe: "Alfa-2", status: "DISPONIVEL" },
    { id: "vtr-03", prefixo: "VTR-1203", placa: "IVX-3C42", equipe: "Bravo-1", status: "DISPONIVEL" },
    { id: "vtr-04", prefixo: "VTR-1204", placa: "IVX-4D53", equipe: "Bravo-2", status: "DISPONIVEL" },
    // Viatura que o simulador deixa "sem sinal" periodicamente (demonstra RNF04).
    { id: "vtr-05", prefixo: "VTR-1205", placa: "IVX-5E64", equipe: "Charlie-1", status: "DISPONIVEL" },
    { id: "vtr-06", prefixo: "VTR-1206", placa: "IVX-6F75", equipe: "Charlie-2", status: "INDISPONIVEL" },
  ];
}
