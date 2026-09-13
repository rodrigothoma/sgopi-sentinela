import { NextResponse } from "next/server";
import { atorDaSessao } from "@/adapters/inbound/next/sessao";

export async function GET() {
  const ator = await atorDaSessao();
  return NextResponse.json({ ator }, { status: ator ? 200 : 401 });
}
