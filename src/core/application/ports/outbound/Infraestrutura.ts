import type { EventoDominio } from "@/core/domain/shared/Evento";
import type { NovoRegistroAuditoria, RegistroAuditoria } from "@/core/domain/auditoria/RegistroAuditoria";

export interface PortaRelogio {
  agora(): Date;
}

export interface PortaGeradorId {
  gerar(): string;
}

export interface PortaHash {
  sha256(conteudo: string): string;
}

/** RNF03 — porta de auditoria append-only. */
export interface PortaAuditoria {
  registrar(registro: NovoRegistroAuditoria): Promise<RegistroAuditoria>;
  listar(limite?: number): Promise<RegistroAuditoria[]>;
  /** Percorre a cadeia e informa se algum elo foi adulterado. */
  verificarIntegridade(): Promise<{ integra: boolean; sequenciaCorrompida?: number }>;
}

export type Assinante = (evento: EventoDominio) => void;

/** RNF01 — publicação de eventos consumidos por adaptadores reativos (SSE/WebSocket). */
export interface PublicadorEventos {
  publicar(evento: EventoDominio): void;
  assinar(assinante: Assinante): () => void;
}
