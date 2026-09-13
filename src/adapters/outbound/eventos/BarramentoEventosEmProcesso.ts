import type { Assinante, PublicadorEventos } from "@/core/application/ports/outbound/Infraestrutura";
import type { EventoDominio } from "@/core/domain/shared/Evento";

/**
 * Barramento em processo. Suficiente para uma única instância do Next.js.
 * Para múltiplas instâncias, trocar por adaptador Redis Pub/Sub — o núcleo
 * não muda (RNF05).
 */
export class BarramentoEventosEmProcesso implements PublicadorEventos {
  private readonly assinantes = new Set<Assinante>();

  publicar(evento: EventoDominio): void {
    for (const assinante of this.assinantes) {
      try {
        assinante(evento);
      } catch (erro) {
        // Um assinante com defeito não pode derrubar o caso de uso (RNF04).
        console.error("[eventos] assinante falhou:", erro);
      }
    }
  }

  assinar(assinante: Assinante): () => void {
    this.assinantes.add(assinante);
    return () => this.assinantes.delete(assinante);
  }

  get quantidadeAssinantes(): number {
    return this.assinantes.size;
  }
}
