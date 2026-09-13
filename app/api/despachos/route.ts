import { obterContainer } from "@/config/container";
import { comAtor } from "@/adapters/inbound/http/comAtor";
import { esquemaDespachar } from "@/adapters/inbound/http/esquemas";
import { ok } from "@/adapters/inbound/http/respostas";
import { criarCoordenada } from "@/core/domain/shared/Coordenada";

export async function GET() {
  return comAtor(async (ator) => ok({ despachos: await obterContainer().casosDeUso.consultarDespachos.listar(ator) }))();
}

/** POST /api/despachos — UC02 */
export async function POST(req: Request) {
  const corpo = await req.json();
  return comAtor(async (ator) => {
    const cmd = esquemaDespachar.parse(corpo);
    const ordem = await obterContainer().casosDeUso.despacharViatura.executar(ator, {
      ...cmd,
      posicaoInformada: cmd.posicaoInformada ? criarCoordenada(cmd.posicaoInformada.latitude, cmd.posicaoInformada.longitude) : undefined,
    });
    return ok({ ordem }, 201);
  })();
}
