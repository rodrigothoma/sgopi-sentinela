import { ErroNaoAutorizado } from "@/core/domain/shared/DomainError";
import type { PortaAuditoria } from "../ports/outbound/Infraestrutura";
import type { Ator } from "./Ator";
import { type Acao, papelPodeExecutar } from "./PoliticaAutorizacao";

/**
 * Serviço de aplicação que aplica a matriz RBAC e, em caso de negação,
 * registra a tentativa no log de auditoria (UC04 — Cenário de Exceção I).
 */
export class Autorizador {
  constructor(private readonly auditoria: PortaAuditoria) {}

  async exigir(ator: Ator, acao: Acao, recurso: { tipo: string; id: string }): Promise<void> {
    if (papelPodeExecutar(ator.papel, acao)) return;

    await this.auditoria.registrar({
      atorId: ator.id,
      atorPapel: ator.papel,
      acao,
      recursoTipo: recurso.tipo,
      recursoId: recurso.id,
      resultado: "NEGADO",
      detalhes: { alertaSeguranca: true, motivo: "Papel sem permissão" },
    });
    throw new ErroNaoAutorizado(acao, ator.papel);
  }
}
