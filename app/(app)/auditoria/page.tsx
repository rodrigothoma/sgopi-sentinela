import { redirect } from "next/navigation";
import { obterContainer } from "@/config/container";
import { atorDaSessao } from "@/adapters/inbound/next/sessao";
import { dataHora } from "@app/_lib/formatos";
import { papelPodeExecutar, Acao } from "@/core/application/seguranca/PoliticaAutorizacao";

export const dynamic = "force-dynamic";

/** RNF03 — visualização do log encadeado por hash. */
export default async function Auditoria() {
  const ator = await atorDaSessao();
  if (!ator) redirect("/login");
  if (!papelPodeExecutar(ator.papel, Acao.AUDITORIA_CONSULTAR)) redirect("/ocorrencias");

  const { registros, integra } = await obterContainer().casosDeUso.consultarAuditoria.listar(ator, 200);

  return (
    <main className="conteudo larga">
      <h1>Log de auditoria</h1>
      <div className={`aviso ${integra ? "aviso-ok" : "aviso-erro"}`} style={{ marginBottom: 16 }}>
        {integra ? "✓ Cadeia de hashes íntegra — nenhum registro foi adulterado." : "✗ Cadeia de hashes CORROMPIDA — investigar imediatamente."}
      </div>
      <div className="cartao">
        <table>
          <thead><tr><th>#</th><th>Quando</th><th>Ator</th><th>Papel</th><th>Ação</th><th>Recurso</th><th>Resultado</th><th>Detalhes</th><th>Hash</th></tr></thead>
          <tbody>
            {registros.map((r) => (
              <tr key={r.sequencia} style={r.resultado === "NEGADO" ? { background: "#fef2f2" } : undefined}>
                <td>{r.sequencia}</td>
                <td>{dataHora(r.registradoEm)}</td>
                <td className="mono">{r.atorId}</td>
                <td>{r.atorPapel}</td>
                <td className="mono">{r.acao}</td>
                <td className="mono">{r.recursoTipo}/{r.recursoId.slice(0, 8)}</td>
                <td>{r.resultado}</td>
                <td className="mono" style={{ maxWidth: 320, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{r.detalhes ? JSON.stringify(r.detalhes) : "—"}</td>
                <td className="mono">{r.hash.slice(0, 12)}…</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </main>
  );
}
