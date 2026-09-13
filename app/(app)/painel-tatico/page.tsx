import { redirect } from "next/navigation";
import { atorDaSessao } from "@/adapters/inbound/next/sessao";
import { papelPodeExecutar, Acao } from "@/core/application/seguranca/PoliticaAutorizacao";
import { PainelTatico } from "@app/_componentes/PainelTatico";
import { CENTRO_ALEGRETE } from "@/config/seed";

export default async function PaginaPainelTatico() {
  const ator = await atorDaSessao();
  if (!ator) redirect("/login");
  if (!papelPodeExecutar(ator.papel, Acao.VIATURA_CONSULTAR)) redirect("/ocorrencias");

  return (
    <main className="conteudo larga">
      <h1>Painel tático</h1>
      <p className="sub">UC02 — viaturas em tempo real (telemetria via SSE), sugestão das 3 unidades mais próximas e emissão de ordem de despacho.</p>
      <PainelTatico centro={CENTRO_ALEGRETE} podeDespachar={papelPodeExecutar(ator.papel, Acao.DESPACHO_EMITIR)} />
    </main>
  );
}
