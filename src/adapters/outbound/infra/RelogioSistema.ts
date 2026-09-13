import type { PortaRelogio } from "@/core/application/ports/outbound/Infraestrutura";

export class RelogioSistema implements PortaRelogio {
  agora(): Date {
    return new Date();
  }
}
