"use client";

import dynamic from "next/dynamic";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api, mensagemDeErro } from "@app/_lib/api";
import { dataHora, ROTULO_GRAVIDADE } from "@app/_lib/formatos";
import { SeloGps, SeloStatus, SeloViatura } from "./Selo";
import { recalcularSinal, type OcorrenciaUI, type SugestaoUI, type ViaturaUI } from "./tiposPainel";

// Leaflet só existe no navegador: desliga SSR para este componente.
const MapaTatico = dynamic(() => import("./MapaTatico").then((m) => m.MapaTatico), {
  ssr: false,
  loading: () => <div className="mapa" style={{ display: "grid", placeItems: "center" }}>Carregando mapa…</div>,
});

type EstadoConexao = "conectando" | "conectado" | "reconectando";

interface Props {
  centro: { latitude: number; longitude: number };
  podeDespachar: boolean;
}

export function PainelTatico({ centro, podeDespachar }: Props) {
  const [viaturas, setViaturas] = useState<Map<string, ViaturaUI>>(new Map());
  const [ocorrencias, setOcorrencias] = useState<Map<string, OcorrenciaUI>>(new Map());
  const [conexao, setConexao] = useState<EstadoConexao>("conectando");
  const [falhaMapa, setFalhaMapa] = useState<string | null>(null);
  const [modoTabela, setModoTabela] = useState(false);
  const [selecionadaId, setSelecionadaId] = useState<string | null>(null);
  const [sugestao, setSugestao] = useState<SugestaoUI | null>(null);
  const [carregandoSugestao, setCarregandoSugestao] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [aviso, setAviso] = useState<string | null>(null);
  const [posicaoManual, setPosicaoManual] = useState({ latitude: "", longitude: "" });
  const [despachando, setDespachando] = useState<string | null>(null);
  const [ultimoDespacho, setUltimoDespacho] = useState<string | null>(null);
  const esRef = useRef<EventSource | null>(null);

  // ---- Carga inicial (REST) ----
  const carregar = useCallback(async () => {
    const [{ viaturas: vs }, { ocorrencias: os }] = await Promise.all([
      api<{ viaturas: ViaturaUI[] }>("/api/viaturas"),
      api<{ ocorrencias: OcorrenciaUI[] }>("/api/ocorrencias?status=VALIDADA,EM_ATENDIMENTO"),
    ]);
    setViaturas(new Map(vs.map((v) => [v.id, recalcularSinal(v)])));
    setOcorrencias(new Map(os.map((o) => [o.id, o])));
  }, []);

  // ---- Fluxo em tempo real (SSE) ----
  useEffect(() => {
    let ativo = true;
    void carregar().catch((e) => setErro(mensagemDeErro(e)));

    const es = new EventSource("/api/eventos");
    esRef.current = es;
    es.addEventListener("conectado", () => ativo && setConexao("conectado"));
    es.onerror = () => {
      if (!ativo) return;
      // EventSource reconecta sozinho; ao voltar, recarregamos o estado para não perder eventos.
      setConexao("reconectando");
    };
    es.onopen = () => {
      if (!ativo) return;
      setConexao("conectado");
      void carregar().catch(() => undefined);
    };

    es.addEventListener("viatura.posicao", (ev) => {
      const p = JSON.parse((ev as MessageEvent).data) as { viaturaId: string; prefixo: string; status: ViaturaUI["status"]; coordenada: { latitude: number; longitude: number }; recebidaEm: string };
      setViaturas((atual) => {
        const prox = new Map(atual);
        const v = prox.get(p.viaturaId);
        prox.set(p.viaturaId, recalcularSinal({
          ...(v ?? { id: p.viaturaId, prefixo: p.prefixo, placa: "", equipe: "", status: p.status, sinalGpsValido: true }),
          status: p.status,
          ultimaPosicao: { coordenada: p.coordenada, recebidaEm: p.recebidaEm },
        }));
        return prox;
      });
    });

    es.addEventListener("ocorrencia.alterada", (ev) => {
      const p = JSON.parse((ev as MessageEvent).data) as { ocorrenciaId: string; status: OcorrenciaUI["status"] };
      // Entradas/saídas do painel dependem de dados completos → recarrega a lista.
      if (p.status === "VALIDADA" || p.status === "EM_ATENDIMENTO" || p.status === "CONCLUIDA") {
        void api<{ ocorrencias: OcorrenciaUI[] }>("/api/ocorrencias?status=VALIDADA,EM_ATENDIMENTO")
          .then(({ ocorrencias: os }) => setOcorrencias(new Map(os.map((o) => [o.id, o]))))
          .catch(() => undefined);
      }
    });

    es.addEventListener("viatura.despachada", (ev) => {
      const p = JSON.parse((ev as MessageEvent).data) as { viaturaId: string; prefixo: string; protocolo: string };
      setViaturas((atual) => {
        const prox = new Map(atual);
        const v = prox.get(p.viaturaId);
        if (v) prox.set(p.viaturaId, { ...v, status: "EM_DESLOCAMENTO" });
        return prox;
      });
      setUltimoDespacho(`${p.prefixo} despachada para ${p.protocolo}`);
    });

    return () => {
      ativo = false;
      es.close();
    };
  }, [carregar]);

  // ---- Reavalia validade do GPS a cada segundo (RNF04) ----
  useEffect(() => {
    const t = setInterval(() => {
      setViaturas((atual) => {
        let mudou = false;
        const prox = new Map<string, ViaturaUI>();
        for (const [id, v] of atual) {
          const r = recalcularSinal(v);
          if (r !== v) mudou = true;
          prox.set(id, r);
        }
        return mudou ? prox : atual;
      });
    }, 1000);
    return () => clearInterval(t);
  }, []);

  // ---- Sugestões para a ocorrência selecionada (UC02 passo 4) ----
  useEffect(() => {
    setSugestao(null);
    setAviso(null);
    if (!selecionadaId) return;
    const o = ocorrencias.get(selecionadaId);
    if (!o || o.status !== "VALIDADA") return;
    let cancelado = false;
    setCarregandoSugestao(true);
    api<SugestaoUI>(`/api/despachos/sugestoes?ocorrenciaId=${encodeURIComponent(selecionadaId)}`)
      .then((s) => { if (!cancelado) setSugestao(s); })
      .catch((e) => { if (!cancelado) setErro(mensagemDeErro(e)); })
      .finally(() => { if (!cancelado) setCarregandoSugestao(false); });
    return () => { cancelado = true; };
  }, [selecionadaId, ocorrencias]);

  async function despachar(viaturaId: string, precisaPosicaoManual: boolean) {
    if (!selecionadaId) return;
    setErro(null);
    setDespachando(viaturaId);
    try {
      const posicaoInformada = precisaPosicaoManual
        ? { latitude: Number(posicaoManual.latitude), longitude: Number(posicaoManual.longitude) }
        : undefined;
      if (precisaPosicaoManual && (!Number.isFinite(posicaoInformada!.latitude) || !Number.isFinite(posicaoInformada!.longitude) || posicaoManual.latitude === "")) {
        throw new Error("Informe latitude e longitude relatadas via rádio para o despacho manual.");
      }
      await api("/api/despachos", { method: "POST", json: { ocorrenciaId: selecionadaId, viaturaId, posicaoInformada } });
      setSelecionadaId(null);
      setPosicaoManual({ latitude: "", longitude: "" });
      await carregar();
    } catch (e) {
      setErro(mensagemDeErro(e));
    } finally {
      setDespachando(null);
    }
  }

  const listaViaturas = useMemo(() => [...viaturas.values()].sort((a, b) => a.prefixo.localeCompare(b.prefixo)), [viaturas]);
  const listaOcorrencias = useMemo(
    () => [...ocorrencias.values()].sort((a, b) => (a.status === b.status ? b.gravidade - a.gravidade : a.status === "VALIDADA" ? -1 : 1)),
    [ocorrencias],
  );
  const semSinal = listaViaturas.filter((v) => v.status !== "INDISPONIVEL" && !v.sinalGpsValido);
  const selecionada = selecionadaId ? ocorrencias.get(selecionadaId) : undefined;
  const exibirTabela = modoTabela || !!falhaMapa;

  return (
    <>
      <div className="acoes" style={{ marginBottom: 12 }}>
        <span className={`selo ${conexao === "conectado" ? "selo-gps-ok" : "selo-gps-falha"}`}>
          {conexao === "conectado" ? "● Telemetria conectada (SSE)" : conexao === "conectando" ? "○ Conectando…" : "○ Reconectando…"}
        </span>
        <button className="secundario pequeno" onClick={() => setModoTabela((m) => !m)} disabled={!!falhaMapa}>
          {exibirTabela ? "Ver mapa" : "Ver listagem tabular"}
        </button>
        {ultimoDespacho && <span className="pequeno">Último despacho: {ultimoDespacho}</span>}
      </div>

      {falhaMapa && <div className="aviso aviso-alerta" style={{ marginBottom: 12 }}>⚠ {falhaMapa} Exibindo listagem tabular (RNF04).</div>}
      {semSinal.length > 0 && (
        <div className="aviso aviso-alerta" style={{ marginBottom: 12 }}>
          ⚠ Falha de sinal GPS ({semSinal.map((v) => v.prefixo).join(", ")}): despacho automático bloqueado para estas unidades; use a última posição conhecida ou informe a posição via rádio.
        </div>
      )}
      {erro && <div className="aviso aviso-erro" style={{ marginBottom: 12 }}>{erro}</div>}

      <div className="grade-2">
        <div>
          {exibirTabela ? (
            <div className="cartao">
              <h2 style={{ marginTop: 0 }}>Viaturas — última posição conhecida</h2>
              <table>
                <thead><tr><th>Prefixo</th><th>Equipe</th><th>Status</th><th>GPS</th><th>Lat/Lng</th><th>Última posição em</th></tr></thead>
                <tbody>
                  {listaViaturas.map((v) => (
                    <tr key={v.id}>
                      <td className="mono">{v.prefixo}</td><td>{v.equipe}</td>
                      <td><SeloViatura status={v.status} /></td>
                      <td><SeloGps valido={v.sinalGpsValido} /></td>
                      <td className="mono">{v.ultimaPosicao ? `${v.ultimaPosicao.coordenada.latitude.toFixed(5)}, ${v.ultimaPosicao.coordenada.longitude.toFixed(5)}` : "—"}</td>
                      <td>{dataHora(v.ultimaPosicao?.recebidaEm)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <>
              <MapaTatico
                centro={centro}
                viaturas={listaViaturas}
                ocorrencias={listaOcorrencias}
                ocorrenciaSelecionadaId={selecionadaId}
                onSelecionarOcorrencia={setSelecionadaId}
                onFalhaMapa={setFalhaMapa}
              />
              <div className="legenda">
                <span className="l-disp">Viatura disponível</span>
                <span className="l-desl">Em deslocamento</span>
                <span className="l-falha">Sem sinal GPS (&gt; 60 s)</span>
                <span className="l-oco">Ocorrência validada</span>
              </div>
            </>
          )}

          <div className="cartao" style={{ marginTop: 16 }}>
            <h2 style={{ marginTop: 0 }}>Ocorrências pendentes de atendimento</h2>
            {listaOcorrencias.length === 0 ? <p className="pequeno">Nenhuma ocorrência validada aguardando despacho.</p> : (
              <table>
                <thead><tr><th>Protocolo</th><th>Tipificação</th><th>Bairro</th><th>Gravidade</th><th>Status</th></tr></thead>
                <tbody>
                  {listaOcorrencias.map((o) => (
                    <tr key={o.id} className="clicavel" onClick={() => setSelecionadaId(o.id)} style={o.id === selecionadaId ? { background: "#eef2ff" } : undefined}>
                      <td className="mono">{o.protocolo}</td><td>{o.tipificacao}</td><td>{o.endereco.bairro}</td>
                      <td>{ROTULO_GRAVIDADE[o.gravidade]}</td><td><SeloStatus status={o.status} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        <div>
          <div className="cartao">
            <h2 style={{ marginTop: 0 }}>Despacho</h2>
            {!selecionada && <p className="pequeno">Selecione uma ocorrência validada (na lista ou no mapa) para ver as viaturas mais próximas.</p>}
            {selecionada && (
              <>
                <dl>
                  <dt>Protocolo</dt><dd className="mono">{selecionada.protocolo}</dd>
                  <dt>Tipificação</dt><dd>{selecionada.tipificacao}</dd>
                  <dt>Local</dt><dd>{selecionada.endereco.logradouro}, {selecionada.endereco.bairro}</dd>
                  <dt>Status</dt><dd><SeloStatus status={selecionada.status} /></dd>
                </dl>
                {selecionada.status !== "VALIDADA" && <p className="aviso aviso-info" style={{ marginTop: 12 }}>Ocorrência já em atendimento.</p>}
                {selecionada.status === "VALIDADA" && !selecionada.coordenada && (
                  <p className="aviso aviso-alerta" style={{ marginTop: 12 }}>Ocorrência sem coordenada: distâncias não podem ser calculadas.</p>
                )}
                {carregandoSugestao && <p className="pequeno">Calculando proximidade…</p>}
                {sugestao && (
                  <>
                    {sugestao.despachoAutomaticoBloqueado && (
                      <div className="aviso aviso-alerta" style={{ margin: "12px 0" }}>
                        Nenhuma viatura disponível possui GPS válido. Despacho automático bloqueado — informe a posição via rádio (RNF04).
                      </div>
                    )}
                    {sugestao.sugestoes.length === 0 && (
                      <div className="aviso aviso-erro" style={{ margin: "12px 0" }}>Nenhuma viatura disponível. A ocorrência permanece na fila com prioridade máxima.</div>
                    )}
                    <h2>Viaturas sugeridas</h2>
                    <table>
                      <thead><tr><th>Viatura</th><th>Distância</th><th>GPS</th><th></th></tr></thead>
                      <tbody>
                        {sugestao.sugestoes.map((s) => {
                          const precisaManual = !s.viatura.sinalGpsValido;
                          return (
                            <tr key={s.viatura.id}>
                              <td><strong className="mono">{s.viatura.prefixo}</strong><br /><span className="pequeno">{s.viatura.equipe}</span></td>
                              <td>{s.distanciaKm !== null ? `${s.distanciaKm.toFixed(2)} km` : "—"}</td>
                              <td><SeloGps valido={s.viatura.sinalGpsValido} /></td>
                              <td>
                                {podeDespachar && (
                                  <button className="pequeno" disabled={despachando !== null} onClick={() => void despachar(s.viatura.id, precisaManual)}>
                                    {despachando === s.viatura.id ? "…" : precisaManual ? "Despacho manual" : "Despachar"}
                                  </button>
                                )}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                    {sugestao.sugestoes.some((s) => !s.viatura.sinalGpsValido) && podeDespachar && (
                      <div style={{ marginTop: 12 }}>
                        <span className="pequeno">Posição informada via rádio (obrigatória para viaturas sem GPS):</span>
                        <div className="linha" style={{ marginTop: 6 }}>
                          <label>Latitude<input value={posicaoManual.latitude} onChange={(e) => setPosicaoManual({ ...posicaoManual, latitude: e.target.value })} inputMode="decimal" placeholder="-29.78" /></label>
                          <label>Longitude<input value={posicaoManual.longitude} onChange={(e) => setPosicaoManual({ ...posicaoManual, longitude: e.target.value })} inputMode="decimal" placeholder="-55.79" /></label>
                        </div>
                      </div>
                    )}
                    {!podeDespachar && <p className="pequeno" style={{ marginTop: 8 }}>Seu perfil pode visualizar, mas apenas o Operador de Central emite despachos (RNF02).</p>}
                  </>
                )}
              </>
            )}
          </div>

          <div className="cartao" style={{ marginTop: 16 }}>
            <h2 style={{ marginTop: 0 }}>Frota</h2>
            <table>
              <thead><tr><th>Viatura</th><th>Status</th><th>GPS</th></tr></thead>
              <tbody>
                {listaViaturas.map((v) => (
                  <tr key={v.id}><td className="mono">{v.prefixo}</td><td><SeloViatura status={v.status} /></td><td><SeloGps valido={v.sinalGpsValido} /></td></tr>
                ))}
              </tbody>
            </table>
          </div>
          {aviso && <div className="aviso aviso-info" style={{ marginTop: 12 }}>{aviso}</div>}
        </div>
      </div>
    </>
  );
}
