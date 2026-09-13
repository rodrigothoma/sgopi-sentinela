import type { NextResponse } from "next/server";
import type { Ator } from "@/core/application/seguranca/Ator";
import { atorDaSessao } from "@/adapters/inbound/next/sessao";
import { naoAutenticado, respostaErro } from "./respostas";

/**
 * Envolve um handler exigindo sessão válida e convertendo erros de domínio
 * em respostas HTTP. Mantém os route handlers do `app/api` triviais.
 */
export function comAtor(handler: (ator: Ator) => Promise<NextResponse>): () => Promise<NextResponse> {
  return async () => {
    const ator = await atorDaSessao();
    if (!ator) return naoAutenticado();
    try {
      return await handler(ator);
    } catch (erro) {
      return respostaErro(erro);
    }
  };
}
