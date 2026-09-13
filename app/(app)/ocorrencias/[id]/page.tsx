import { notFound, redirect } from "next/navigation";
import { obterContainer } from "@/config/container";
import { atorDaSessao } from "@/adapters/inbound/next/sessao";
import { ehErroDominio } from "@/core/domain/shared/DomainError";
import { ROTULO_STATUS } from "@/core/domain/ocorrencia/StatusOcorrencia";
import { SeloStatus } from "@app/_componentes/Selo";
import { AcoesOcorrencia } from "@app/_componentes/AcoesOcorrencia";
import { dataHora, ROTULO_GRAVIDADE, serializar } from "@app/_lib/formatos";

export const dynamic = "force-dynamic";

const ROTULO_ENVOLVIDO: Record<string, string> = { VITIMA: "Vítima", TESTEMUNHA: "Testemunha", SUSPEITO: "Suspeito" };

export default async function DetalheOcorrencia({
  params, searchParams,
}: { params: Promise<{ id: string }>; searchParams: Promise<{ registrada?: string }> }) {
  const ator = await atorDaSessao();
  if (!ator) redirect("/login");
  const { id } = await params;
  const { registrada } = await searchParams;

  const c = obterContainer();
  let ocorrencia;
  try {
    ocorrencia = await c.casosDeUso.consultarOcorrencias.obter(ator, id);
  } catch (e) {
    if (ehErroDominio(e) && e.codigo === "NAO_ENCONTRADO") notFound();
    throw e;
  }
  const despachos = ator.papel === "AGENTE" ? [] : await c.casosDeUso.consultarDespachos.listar(ator).catch(() => []);
  const despachosDesta = despachos.filter((d) => d.ocorrenciaId === id);

  return (
    <main className="conteudo">
      {registrada && (
        <div className="aviso aviso-ok" style={{ marginBottom: 16 }}>
          Ocorrência registrada com sucesso. Protocolo <strong className="mono">{ocorrencia.protocolo}</strong> — aguardando revisão do Delegado.
        </div>
      )}
      <div className="acoes" style={{ justifyContent: "space-between" }}>
        <h1><span className="mono">{ocorrencia.protocolo}</span> — {ocorrencia.tipificacao}</h1>
        <SeloStatus status={ocorrencia.status} />
      </div>

      <div className="grade-2">
        <div>
          <section className="cartao">
            <h2 style={{ marginTop: 0 }}>Narrativa do fato</h2>
            <pre className="narrativa">{ocorrencia.descricaoFato}</pre>
            {ocorrencia.hashIntegridade && (
              <p className="pequeno">🔒 Narrativa selada na validação — SHA-256 <span className="mono">{ocorrencia.hashIntegridade.slice(0, 16)}…</span> (UC04 RN2 / RNF03)</p>
            )}
          </section>

          <section className="cartao">
            <h2 style={{ marginTop: 0 }}>Envolvidos</h2>
            <table>
              <thead><tr><th>Nome</th><th>Tipo</th><th>Documento</th><th>Observações</th></tr></thead>
              <tbody>
                {ocorrencia.envolvidos.map((e) => (
                  <tr key={e.id}><td>{e.nome}</td><td>{ROTULO_ENVOLVIDO[e.tipo]}</td><td className="mono">{e.documento ?? "—"}</td><td>{e.observacoes ?? "—"}</td></tr>
                ))}
              </tbody>
            </table>
          </section>

          <section className="cartao">
            <h2 style={{ marginTop: 0 }}>Evidências digitais</h2>
            {ocorrencia.evidencias.length === 0 ? <p className="pequeno">Nenhuma evidência anexada.</p> : (
              <table>
                <thead><tr><th>Arquivo</th><th>Tipo</th><th>Tamanho</th><th>Hash (SHA-256)</th></tr></thead>
                <tbody>
                  {ocorrencia.evidencias.map((ev) => (
                    <tr key={ev.id}><td>{ev.nomeArquivo}</td><td>{ev.tipoMime}</td><td>{(ev.tamanhoBytes / 1024).toFixed(1)} KB</td><td className="mono">{ev.hashConteudo.slice(0, 20)}…</td></tr>
                  ))}
                </tbody>
              </table>
            )}
          </section>

          <AcoesOcorrencia ator={ator} ocorrencia={serializar(ocorrencia)} />
        </div>

        <div>
          <section className="cartao">
            <h2 style={{ marginTop: 0 }}>Dados gerais</h2>
            <dl>
              <dt>Gravidade</dt><dd>{ROTULO_GRAVIDADE[ocorrencia.gravidade]}</dd>
              <dt>Endereço</dt><dd>{ocorrencia.endereco.logradouro}{ocorrencia.endereco.numero ? `, ${ocorrencia.endereco.numero}` : ""}<br />{ocorrencia.endereco.bairro} — {ocorrencia.endereco.cidade}/{ocorrencia.endereco.uf}</dd>
              <dt>Coordenada</dt><dd className="mono">{ocorrencia.coordenada ? `${ocorrencia.coordenada.latitude.toFixed(5)}, ${ocorrencia.coordenada.longitude.toFixed(5)}` : "não informada"}</dd>
              <dt>Agente</dt><dd className="mono">{ocorrencia.agenteId}</dd>
              <dt>Registrada em</dt><dd>{dataHora(ocorrencia.criadaEm)}</dd>
              {ocorrencia.delegadoId && <><dt>Delegado</dt><dd className="mono">{ocorrencia.delegadoId}</dd></>}
              {ocorrencia.despachoAutoridade && <><dt>Despacho da autoridade</dt><dd>{ocorrencia.despachoAutoridade}</dd></>}
              {ocorrencia.pendenciasCorrecao && <><dt>Pendências</dt><dd style={{ color: "var(--perigo)" }}>{ocorrencia.pendenciasCorrecao}</dd></>}
            </dl>
          </section>

          <section className="cartao">
            <h2 style={{ marginTop: 0 }}>Histórico de status</h2>
            <ul className="lista-simples">
              {ocorrencia.historico.map((h, i) => (
                <li key={i}>
                  <strong>{ROTULO_STATUS[h.para]}</strong> <span className="pequeno">— {dataHora(h.em)} por <span className="mono">{h.autorId}</span>{h.motivo ? ` — ${h.motivo}` : ""}</span>
                </li>
              ))}
            </ul>
          </section>

          {despachosDesta.length > 0 && (
            <section className="cartao">
              <h2 style={{ marginTop: 0 }}>Ordens de despacho</h2>
              <ul className="lista-simples">
                {despachosDesta.map((d) => (
                  <li key={d.id}><strong>{d.prefixoViatura}</strong> — {dataHora(d.emitidaEm)} · {d.modo === "AUTOMATICO" ? "automático" : "manual (posição via rádio)"}{d.distanciaKm !== undefined ? ` · ${d.distanciaKm.toFixed(2)} km` : ""}</li>
                ))}
              </ul>
            </section>
          )}
        </div>
      </div>
    </main>
  );
}
