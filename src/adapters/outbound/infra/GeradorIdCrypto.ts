import { randomUUID } from "node:crypto";
import type { PortaGeradorId } from "@/core/application/ports/outbound/Infraestrutura";

export class GeradorIdCrypto implements PortaGeradorId {
  gerar(): string {
    return randomUUID();
  }
}
