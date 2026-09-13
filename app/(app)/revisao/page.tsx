import Link from "next/link";
import { redirect } from "next/navigation";
import { obterContainer } from "@/config/container";
import { atorDaSessao } from "@/adapters/inbound/next/sessao";
import { dataHora, ROTULO_GRAVIDADE } from "@app/_lib/formatos";

export const dynamic = "force-dynamic";

/** UC04 passos 1–2: fila de triagem ordenada por gravidade e antiguidade. */
export default async function FilaRevisao() {
  const ator = await atorDaSessao();
  if (!ator) redirect("/login");
  if (ator.papel !== "DELEGADO") redirect("/ocorrencias");

  const fila = await obterContainer().casosDeUso.consultarOcorrencias.listar(ator, { status: ["AGUARDANDO_REVISAO"] });

  return (
    <main className="conteudo">
      <h1>Fila de revisão</h1>
      <p className="sub">{fila.length} ocorrência(s) aguardando validação, ordenadas por gravidade e antiguidade.</p>
      <div className="cartao">
        {fila.length === 0 ? <p className="pequeno">Fila vazia.</p> : (
          <table>
            <thead><tr><th>Protocolo</th><th>Tipificação</th><th>Gravidade</th><th>Envolvidos</th><th>Aguardando desde</th><th></th></tr></thead>
            <tbody>
              {fila.map((o) => (
                <tr key={o.id}>
                  <td className="mono">{o.protocolo}</td>
                  <td>{o.tipificacao}</td>
                  <td>{ROTULO_GRAVIDADE[o.gravidade]}</td>
                  <td>{o.envolvidos.length}</td>
                  <td>{dataHora(o.criadaEm)}</td>
                  <td><Link className="botao" href={`/ocorrencias/${o.id}`}>Analisar</Link></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </main>
  );
}
