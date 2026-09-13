import { NextResponse } from "next/server";
import { obterContainer } from "@/config/container";
import { comAtor } from "@/adapters/inbound/http/comAtor";
import { ok } from "@/adapters/inbound/http/respostas";

/** GET /api/despachos/sugestoes?ocorrenciaId=... — UC02 passo 4 */
export async function GET(req: Request) {
  const ocorrenciaId = new URL(req.url).searchParams.get("ocorrenciaId");
  if (!ocorrenciaId) {
    return NextResponse.json({ erro: { codigo: "VALIDACAO", mensagem: "ocorrenciaId é obrigatório." } }, { status: 400 });
  }
  return comAtor(async (ator) => ok(await obterContainer().casosDeUso.sugerirViaturas.executar(ator, ocorrenciaId, 3)))();
}
