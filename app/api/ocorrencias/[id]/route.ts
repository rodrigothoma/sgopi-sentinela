import { obterContainer } from "@/config/container";
import { comAtor } from "@/adapters/inbound/http/comAtor";
import { ok } from "@/adapters/inbound/http/respostas";

export async function GET(_req: Request, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params;
  return comAtor(async (ator) => {
    const ocorrencia = await obterContainer().casosDeUso.consultarOcorrencias.obter(ator, id);
    return ok({ ocorrencia });
  })();
}
