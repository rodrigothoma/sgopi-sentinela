import { NextResponse } from "next/server";
import { obterContainer } from "@/config/container";
import { esquemaTelemetria } from "@/adapters/inbound/http/esquemas";
import { respostaErro } from "@/adapters/inbound/http/respostas";
import { ATOR_SISTEMA } from "@/core/application/seguranca/Ator";
import { criarCoordenada } from "@/core/domain/shared/Coordenada";

/**
 * POST /api/viaturas/:id/telemetria
 * Porta HTTP para hardware GPS externo (ou simuladores externos). Autenticada
 * por token de serviço, não por sessão de usuário.
 */
export async function POST(req: Request, ctx: { params: Promise<{ id: string }> }) {
  const token = req.headers.get("x-telemetria-token");
  if (token !== (process.env.TELEMETRIA_TOKEN ?? "token-telemetria-dev")) {
    return NextResponse.json({ erro: { codigo: "NAO_AUTENTICADO", mensagem: "Token de telemetria inválido." } }, { status: 401 });
  }
  try {
    const { id } = await ctx.params;
    const { coordenada, recebidaEm } = esquemaTelemetria.parse(await req.json());
    await obterContainer().casosDeUso.atualizarTelemetria.executar(
      ATOR_SISTEMA, id, criarCoordenada(coordenada.latitude, coordenada.longitude), recebidaEm ? new Date(recebidaEm) : undefined,
    );
    return NextResponse.json({ ok: true }, { status: 202 });
  } catch (erro) {
    return respostaErro(erro);
  }
}
