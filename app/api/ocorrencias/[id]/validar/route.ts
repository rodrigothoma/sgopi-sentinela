import { obterContainer } from "@/config/container";
import { comAtor } from "@/adapters/inbound/http/comAtor";
import { esquemaValidar } from "@/adapters/inbound/http/esquemas";
import { ok } from "@/adapters/inbound/http/respostas";

/** POST /api/ocorrencias/:id/validar — UC04 (somente DELEGADO) */
export async function POST(req: Request, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params;
  const corpo = await req.json();
  return comAtor(async (ator) => {
    const { despachoAutoridade } = esquemaValidar.parse(corpo);
    const ocorrencia = await obterContainer().casosDeUso.validarOcorrencia.executar(ator, id, despachoAutoridade);
    return ok({ ocorrencia });
  })();
}
