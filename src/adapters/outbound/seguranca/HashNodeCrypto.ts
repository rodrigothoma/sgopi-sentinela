import { createHash } from "node:crypto";
import type { PortaHash } from "@/core/application/ports/outbound/Infraestrutura";

export class HashNodeCrypto implements PortaHash {
  sha256(conteudo: string): string {
    return createHash("sha256").update(conteudo, "utf8").digest("hex");
  }
}
