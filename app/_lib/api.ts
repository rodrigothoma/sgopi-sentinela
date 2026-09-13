"use client";

/** Cliente HTTP mínimo usado pelos componentes React (adaptador UI → REST). */
export interface ErroApi { codigo: string; mensagem: string; detalhes?: Record<string, unknown> | null }

export class RespostaErroApi extends Error {
  constructor(public readonly status: number, public readonly erro: ErroApi) {
    super(erro.mensagem);
  }
}

export async function api<T>(caminho: string, init?: RequestInit & { json?: unknown }): Promise<T> {
  const { json, ...resto } = init ?? {};
  const resp = await fetch(caminho, {
    ...resto,
    headers: { ...(json !== undefined ? { "Content-Type": "application/json" } : {}), ...(resto.headers ?? {}) },
    body: json !== undefined ? JSON.stringify(json) : resto.body,
    cache: "no-store",
  });
  const corpo = (await resp.json().catch(() => ({}))) as { erro?: ErroApi } & T;
  if (!resp.ok) {
    throw new RespostaErroApi(resp.status, corpo.erro ?? { codigo: "DESCONHECIDO", mensagem: `HTTP ${resp.status}` });
  }
  return corpo;
}

export function mensagemDeErro(e: unknown): string {
  if (e instanceof RespostaErroApi) {
    const campos = (e.erro.detalhes?.camposFaltantes as string[] | undefined)?.join(", ");
    return campos ? `${e.erro.mensagem} Campos: ${campos}` : e.erro.mensagem;
  }
  return e instanceof Error ? e.message : "Erro inesperado.";
}
