import { obterContainer } from "@/config/container";
import { comAtor } from "@/adapters/inbound/http/comAtor";
import { ok } from "@/adapters/inbound/http/respostas";

export async function GET(req: Request) {
  const limite = Number(new URL(req.url).searchParams.get("limite") ?? 100);
  return comAtor(async (ator) => ok(await obterContainer().casosDeUso.consultarAuditoria.listar(ator, limite)))();
}
