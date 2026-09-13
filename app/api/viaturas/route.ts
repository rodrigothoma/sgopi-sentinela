import { obterContainer } from "@/config/container";
import { comAtor } from "@/adapters/inbound/http/comAtor";
import { ok } from "@/adapters/inbound/http/respostas";

export async function GET() {
  return comAtor(async (ator) => {
    const viaturas = await obterContainer().casosDeUso.consultarViaturas.listar(ator);
    return ok({ viaturas });
  })();
}
