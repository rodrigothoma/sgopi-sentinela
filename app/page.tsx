import { redirect } from "next/navigation";
import { atorDaSessao } from "@/adapters/inbound/next/sessao";
import { rotaInicialPorPapel } from "@app/_lib/navegacao";

export default async function Inicio() {
  const ator = await atorDaSessao();
  redirect(ator ? rotaInicialPorPapel(ator.papel) : "/login");
}
