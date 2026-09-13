import { obterContainer } from "@/config/container";
import { comAtor } from "@/adapters/inbound/http/comAtor";
import { esquemaCorrigir } from "@/adapters/inbound/http/esquemas";
import { ok } from "@/adapters/inbound/http/respostas";

/** POST /api/ocorrencias/:id/corrigir — Agente sana pendências e reenvia */
export async function POST(req: Request, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params;
  const corpo = await req.json();
  return comAtor(async (ator) => {
    const { descricaoFato } = esquemaCorrigir.parse(corpo);
    const ocorrencia = await obterContainer().casosDeUso.corrigirOcorrencia.executar(ator, id, descricaoFato);
    return ok({ ocorrencia });
  })();
}
