import { createHmac, timingSafeEqual } from "node:crypto";
import { cookies } from "next/headers";
import type { Ator } from "@/core/application/seguranca/Ator";
import { ehPapel } from "@/core/domain/usuario/Papel";

export const NOME_COOKIE_SESSAO = "sgopi_sessao";
const DURACAO_SESSAO_S = 60 * 60 * 8; // 8 h (turno de serviço)

function segredo(): string {
  const s = process.env.SESSION_SECRET;
  if (!s) {
    if (process.env.NODE_ENV === "production") throw new Error("SESSION_SECRET não definido.");
    return "segredo-de-desenvolvimento-inseguro";
  }
  return s;
}

function assinar(payload: string): string {
  return createHmac("sha256", segredo()).update(payload).digest("base64url");
}

interface PayloadSessao extends Ator {
  readonly exp: number;
}

/** Codifica a sessão como `base64url(json).hmac`. Sem dependência de libs JWT. */
export function criarTokenSessao(ator: Ator, agora = Date.now()): string {
  const payload: PayloadSessao = { ...ator, exp: Math.floor(agora / 1000) + DURACAO_SESSAO_S };
  const corpo = Buffer.from(JSON.stringify(payload), "utf8").toString("base64url");
  return `${corpo}.${assinar(corpo)}`;
}

export function lerTokenSessao(token: string | undefined, agora = Date.now()): Ator | null {
  if (!token) return null;
  const [corpo, assinatura] = token.split(".");
  if (!corpo || !assinatura) return null;

  const esperada = assinar(corpo);
  const a = Buffer.from(assinatura);
  const b = Buffer.from(esperada);
  if (a.length !== b.length || !timingSafeEqual(a, b)) return null;

  try {
    const p = JSON.parse(Buffer.from(corpo, "base64url").toString("utf8")) as Partial<PayloadSessao>;
    if (!p.id || !p.nome || !ehPapel(p.papel) || typeof p.exp !== "number") return null;
    if (p.exp * 1000 < agora) return null;
    return { id: p.id, nome: p.nome, papel: p.papel };
  } catch {
    return null;
  }
}

export async function atorDaSessao(): Promise<Ator | null> {
  const jar = await cookies();
  return lerTokenSessao(jar.get(NOME_COOKIE_SESSAO)?.value);
}

export async function gravarSessao(ator: Ator): Promise<void> {
  const jar = await cookies();
  jar.set(NOME_COOKIE_SESSAO, criarTokenSessao(ator), {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: DURACAO_SESSAO_S,
  });
}

export async function encerrarSessao(): Promise<void> {
  const jar = await cookies();
  jar.delete(NOME_COOKIE_SESSAO);
}
