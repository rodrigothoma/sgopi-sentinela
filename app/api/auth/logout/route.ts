import { NextResponse } from "next/server";
import { encerrarSessao } from "@/adapters/inbound/next/sessao";

export async function POST() {
  await encerrarSessao();
  return NextResponse.json({ ok: true });
}
