import { obterContainer } from "@/config/container";
import { criarFluxoSse } from "@/adapters/inbound/sse/fluxoEventos";
import { atorDaSessao } from "@/adapters/inbound/next/sessao";
import { naoAutenticado } from "@/adapters/inbound/http/respostas";
import { papelPodeExecutar, Acao } from "@/core/application/seguranca/PoliticaAutorizacao";

export const dynamic = "force-dynamic";

/** GET /api/eventos — fluxo SSE do painel tático (RNF01). */
export async function GET(req: Request) {
  const ator = await atorDaSessao();
  if (!ator) return naoAutenticado();
  if (!papelPodeExecutar(ator.papel, Acao.VIATURA_CONSULTAR)) {
    return new Response("Perfil sem acesso ao fluxo tático.", { status: 403 });
  }
  return criarFluxoSse(obterContainer().eventos, req.signal);
}
