import Link from "next/link";
import { redirect } from "next/navigation";
import { obterContainer } from "@/config/container";
import { atorDaSessao } from "@/adapters/inbound/next/sessao";
import { SeloStatus } from "@app/_componentes/Selo";
import { dataHora, ROTULO_GRAVIDADE } from "@app/_lib/formatos";
import { papelPodeExecutar, Acao } from "@/core/application/seguranca/PoliticaAutorizacao";

export const dynamic = "force-dynamic";

export default async function ListaOcorrencias() {
  const ator = await atorDaSessao();
  if (!ator) redirect("/login");
  if (!papelPodeExecutar(ator.papel, Acao.OCORRENCIA_CONSULTAR)) redirect("/login");

  const lista = await obterContainer().casosDeUso.consultarOcorrencias.listar(ator);

  return (
    <main className="conteudo">
      <div className="acoes" style={{ justifyContent: "space-between" }}>
        <h1>Ocorrências</h1>
        {ator.papel === "AGENTE" && <Link className="botao" href="/ocorrencias/nova">+ Registrar ocorrência</Link>}
      </div>
      <div className="cartao">
        {lista.length === 0 ? (
          <p className="pequeno">Nenhuma ocorrência registrada.</p>
        ) : (
          <table>
            <thead>
              <tr><th>Protocolo</th><th>Tipificação</th><th>Local</th><th>Gravidade</th><th>Status</th><th>Registrada em</th></tr>
            </thead>
            <tbody>
              {lista.map((o) => (
                <tr key={o.id}>
                  <td><Link href={`/ocorrencias/${o.id}`} className="mono">{o.protocolo}</Link></td>
                  <td>{o.tipificacao}</td>
                  <td>{o.endereco.logradouro}{o.endereco.numero ? `, ${o.endereco.numero}` : ""} — {o.endereco.bairro}</td>
                  <td>{ROTULO_GRAVIDADE[o.gravidade]}</td>
                  <td><SeloStatus status={o.status} /></td>
                  <td>{dataHora(o.criadaEm)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </main>
  );
}
