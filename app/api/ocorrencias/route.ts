import { obterContainer } from "@/config/container";
import { comAtor } from "@/adapters/inbound/http/comAtor";
import { esquemaRegistrarOcorrencia } from "@/adapters/inbound/http/esquemas";
import { ok } from "@/adapters/inbound/http/respostas";
import type { StatusOcorrencia } from "@/core/domain/ocorrencia/StatusOcorrencia";

/** GET /api/ocorrencias?status=VALIDADA,EM_ATENDIMENTO */
export async function GET(req: Request) {
  const url = new URL(req.url);
  const status = url.searchParams.get("status")?.split(",").filter(Boolean) as StatusOcorrencia[] | undefined;
  return comAtor(async (ator) => {
    const lista = await obterContainer().casosDeUso.consultarOcorrencias.listar(ator, { status });
    return ok({ ocorrencias: lista });
  })();
}

/** POST /api/ocorrencias — UC01 */
export async function POST(req: Request) {
  const corpo = await req.json();
  return comAtor(async (ator) => {
    const comando = esquemaRegistrarOcorrencia.parse(corpo);
    const ocorrencia = await obterContainer().casosDeUso.registrarOcorrencia.executar(ator, comando);
    return ok({ ocorrencia }, 201);
  })();
}
