import type { PortaAuditoria, PortaHash, PortaRelogio } from "@/core/application/ports/outbound/Infraestrutura";
import { conteudoCanonico, type NovoRegistroAuditoria, type RegistroAuditoria } from "@/core/domain/auditoria/RegistroAuditoria";

const HASH_GENESIS = "0".repeat(64);

/**
 * RNF03 — log append-only encadeado por hash. A estrutura de armazenamento é
 * um array em memória no MVP; a mesma lógica serve para uma tabela
 * `auditoria` com constraint de somente-inserção.
 */
export class AuditoriaHashChain implements PortaAuditoria {
  private readonly registros: RegistroAuditoria[] = [];
  private fila: Promise<unknown> = Promise.resolve();

  constructor(private readonly hash: PortaHash, private readonly relogio: PortaRelogio) {}

  registrar(novo: NovoRegistroAuditoria): Promise<RegistroAuditoria> {
    // Serializa as gravações para que a cadeia nunca "bifurque" sob concorrência.
    const tarefa = this.fila.then(() => this.anexar(novo));
    this.fila = tarefa.catch(() => undefined);
    return tarefa;
  }

  private anexar(novo: NovoRegistroAuditoria): RegistroAuditoria {
    const anterior = this.registros.at(-1);
    const semHash: Omit<RegistroAuditoria, "hash"> = {
      ...novo,
      sequencia: (anterior?.sequencia ?? 0) + 1,
      registradoEm: this.relogio.agora(),
      hashAnterior: anterior?.hash ?? HASH_GENESIS,
    };
    const registro: RegistroAuditoria = Object.freeze({ ...semHash, hash: this.hash.sha256(conteudoCanonico(semHash)) });
    this.registros.push(registro);
    return registro;
  }

  async listar(limite = 100): Promise<RegistroAuditoria[]> {
    return this.registros.slice(-limite).reverse();
  }

  async verificarIntegridade(): Promise<{ integra: boolean; sequenciaCorrompida?: number }> {
    let hashAnterior = HASH_GENESIS;
    for (const r of this.registros) {
      const { hash, ...resto } = r;
      if (r.hashAnterior !== hashAnterior || this.hash.sha256(conteudoCanonico(resto)) !== hash) {
        return { integra: false, sequenciaCorrompida: r.sequencia };
      }
      hashAnterior = hash;
    }
    return { integra: true };
  }
}
