import { redirect } from "next/navigation";
import { atorDaSessao } from "@/adapters/inbound/next/sessao";
import { FormularioOcorrencia } from "@app/_componentes/FormularioOcorrencia";

export default async function NovaOcorrencia() {
  const ator = await atorDaSessao();
  if (!ator) redirect("/login");
  if (ator.papel !== "AGENTE") redirect("/ocorrencias");

  return (
    <main className="conteudo">
      <h1>Registrar ocorrência policial</h1>
      <p className="sub">UC01 — a ocorrência será persistida com status <strong>Aguardando Revisão</strong> e enviada à fila do Delegado.</p>
      <FormularioOcorrencia />
    </main>
  );
}
