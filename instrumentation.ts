/**
 * Hook de inicialização do Next.js. Garante que o container (e o simulador
 * de GPS) suba junto com o servidor, antes da primeira requisição.
 */
export async function register() {
  if (process.env.NEXT_RUNTIME === "nodejs") {
    const { obterContainer } = await import("@/config/container");
    obterContainer();
  }
}
