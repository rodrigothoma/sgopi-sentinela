import type { PublicadorEventos } from "@/core/application/ports/outbound/Infraestrutura";

const INTERVALO_HEARTBEAT_MS = 15_000;

/**
 * Adaptador de ENTRADA reativo (RNF01) usando Server-Sent Events.
 *
 * Por que SSE e não WebSocket: Route Handlers do Next.js não expõem o
 * servidor HTTP subjacente, então um servidor WS exigiria um `server.js`
 * customizado (perdendo otimizações do Next). SSE cobre o fluxo servidor→
 * cliente do painel tático com a mesma latência; comandos cliente→servidor
 * continuam via REST. Ver docs/mvp/03-problemas-encontrados.md.
 */
export function criarFluxoSse(eventos: PublicadorEventos, sinal: AbortSignal): Response {
  const codificador = new TextEncoder();

  const stream = new ReadableStream<Uint8Array>({
    start(controlador) {
      const enviar = (nome: string, dados: unknown) => {
        try {
          controlador.enqueue(codificador.encode(`event: ${nome}\ndata: ${JSON.stringify(dados)}\n\n`));
        } catch {
          /* stream já fechado */
        }
      };

      enviar("conectado", { em: new Date().toISOString() });
      const cancelarAssinatura = eventos.assinar((ev) => enviar(ev.tipo, { ...(ev.payload as Record<string, unknown>), ocorridoEm: ev.ocorridoEm.toISOString() }));
      const heartbeat = setInterval(() => {
        try {
          controlador.enqueue(codificador.encode(`: ping\n\n`));
        } catch {
          /* ignorar */
        }
      }, INTERVALO_HEARTBEAT_MS);

      const encerrar = () => {
        clearInterval(heartbeat);
        cancelarAssinatura();
        try {
          controlador.close();
        } catch {
          /* já fechado */
        }
      };
      sinal.addEventListener("abort", encerrar, { once: true });
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream; charset=utf-8",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
      "X-Accel-Buffering": "no",
    },
  });
}
