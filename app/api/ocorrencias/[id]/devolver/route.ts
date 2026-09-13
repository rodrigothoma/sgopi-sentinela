import { obterContainer } from "@/config/container";
import { comAtor } from "@/adapters/inbound/http/comAtor";
import { esquemaDevolver } from "@/adapters/inbound/http/esquemas";
import { ok } from "@/adapters/inbound/http/respostas";

/** POST /api/ocorrencias/:id/devolver — UC04 Cenário Alternativo I */
export async function POST(req: Request, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params;
  const corpo = await req.json();
  return comAtor(async (ator) => {
    const { pendencias } = esquemaDevolver.parse(corpo);
    const ocorrencia = await obterContainer().casosDeUso.devolverOcorrencia.executar(ator, id, pendencias);
    return ok({ ocorrencia });
  })();
}
