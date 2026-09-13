import { NextResponse } from "next/server";
import { ZodError } from "zod";
import { ehErroDominio, type CodigoErroDominio } from "@/core/domain/shared/DomainError";

const STATUS_POR_CODIGO: Record<CodigoErroDominio, number> = {
  VALIDACAO: 422,
  NAO_ENCONTRADO: 404,
  TRANSICAO_INVALIDA: 409,
  NAO_AUTORIZADO: 403,
  CONFLITO: 409,
  PRE_CONDICAO: 412,
};

/** Tradução única de erros de domínio → HTTP. Os casos de uso não conhecem HTTP. */
export function respostaErro(erro: unknown): NextResponse {
  if (ehErroDominio(erro)) {
    return NextResponse.json(
      { erro: { codigo: erro.codigo, mensagem: erro.message, detalhes: erro.detalhes ?? null } },
      { status: STATUS_POR_CODIGO[erro.codigo] },
    );
  }
  if (erro instanceof ZodError || (erro as { name?: string })?.name === "ZodError") {
    const issues = (erro as ZodError).issues;
    return NextResponse.json(
      { erro: { codigo: "VALIDACAO", mensagem: "Corpo da requisição inválido.", detalhes: { issues } } },
      { status: 400 },
    );
  }
  console.error("[http] erro não tratado:", erro);
  return NextResponse.json({ erro: { codigo: "INTERNO", mensagem: "Erro interno do servidor." } }, { status: 500 });
}

export function naoAutenticado(): NextResponse {
  return NextResponse.json({ erro: { codigo: "NAO_AUTENTICADO", mensagem: "Sessão ausente ou expirada." } }, { status: 401 });
}

export function ok<T>(dados: T, status = 200): NextResponse {
  return NextResponse.json(dados, { status });
}
