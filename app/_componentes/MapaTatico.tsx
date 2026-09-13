"use client";

import { useEffect, useRef } from "react";
import "leaflet/dist/leaflet.css";
import type { CircleMarker, Map as LeafletMap, Marker } from "leaflet";
import type { ViaturaUI, OcorrenciaUI } from "./tiposPainel";

interface Props {
  centro: { latitude: number; longitude: number };
  viaturas: ViaturaUI[];
  ocorrencias: OcorrenciaUI[];
  ocorrenciaSelecionadaId: string | null;
  onSelecionarOcorrencia: (id: string) => void;
  onFalhaMapa: (motivo: string) => void;
}

const COR_VIATURA: Record<string, string> = {
  DISPONIVEL: "#16a34a", EM_DESLOCAMENTO: "#7c3aed", EM_ATENDIMENTO: "#0369a1", INDISPONIVEL: "#6b7280",
};

/**
 * Adaptador de UI para o Leaflet. Só roda no cliente (Leaflet acessa `window`),
 * por isso é carregado via `next/dynamic` com `ssr: false`.
 * Usa `circleMarker`/`divIcon` para evitar o problema clássico dos ícones PNG
 * padrão do Leaflet em bundlers.
 */
export function MapaTatico({ centro, viaturas, ocorrencias, ocorrenciaSelecionadaId, onSelecionarOcorrencia, onFalhaMapa }: Props) {
  const divRef = useRef<HTMLDivElement>(null);
  const mapaRef = useRef<LeafletMap | null>(null);
  const leafletRef = useRef<typeof import("leaflet") | null>(null);
  const marcadoresViatura = useRef(new Map<string, CircleMarker>());
  const marcadoresOcorrencia = useRef(new Map<string, Marker>());
  const callbacks = useRef({ onSelecionarOcorrencia, onFalhaMapa });
  callbacks.current = { onSelecionarOcorrencia, onFalhaMapa };

  // Inicialização única do mapa.
  useEffect(() => {
    let cancelado = false;
    (async () => {
      try {
        const L = (await import("leaflet")).default;
        if (cancelado || !divRef.current || mapaRef.current) return;
        leafletRef.current = L;

        const mapa = L.map(divRef.current, { zoomControl: true }).setView([centro.latitude, centro.longitude], 14);
        const tiles = L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
          maxZoom: 19,
          attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        });

        // RNF04: se nenhum tile carregar e vários falharem, sinaliza falha do
        // servidor de mapas para que o painel troque para a listagem tabular.
        let carregados = 0;
        let falhas = 0;
        tiles.on("tileload", () => { carregados += 1; });
        tiles.on("tileerror", () => {
          falhas += 1;
          if (carregados === 0 && falhas >= 4) callbacks.current.onFalhaMapa("Servidor de mapas (OpenStreetMap) inacessível.");
        });
        tiles.addTo(mapa);
        mapaRef.current = mapa;
      } catch (e) {
        callbacks.current.onFalhaMapa(`Falha ao inicializar o mapa: ${e instanceof Error ? e.message : String(e)}`);
      }
    })();
    return () => {
      cancelado = true;
      mapaRef.current?.remove();
      mapaRef.current = null;
      marcadoresViatura.current.clear();
      marcadoresOcorrencia.current.clear();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Sincroniza marcadores de viaturas.
  useEffect(() => {
    const L = leafletRef.current;
    const mapa = mapaRef.current;
    if (!L || !mapa) return;

    const vistos = new Set<string>();
    for (const v of viaturas) {
      if (!v.ultimaPosicao) continue;
      vistos.add(v.id);
      const { latitude, longitude } = v.ultimaPosicao.coordenada;
      // UC02 Exceção I: sinal desatualizado é sinalizado em amarelo.
      const cor = v.sinalGpsValido ? (COR_VIATURA[v.status] ?? "#111") : "#f59e0b";
      const tooltip = `${v.prefixo} · ${v.status}${v.sinalGpsValido ? "" : " · SEM SINAL GPS"}`;

      let m = marcadoresViatura.current.get(v.id);
      if (!m) {
        m = L.circleMarker([latitude, longitude], { radius: 9, weight: 2, color: "#fff", fillColor: cor, fillOpacity: 0.95 })
          .bindTooltip(tooltip, { direction: "top", offset: [0, -8] })
          .addTo(mapa);
        marcadoresViatura.current.set(v.id, m);
      } else {
        m.setLatLng([latitude, longitude]);
        m.setStyle({ fillColor: cor });
        m.setTooltipContent(tooltip);
      }
    }
    for (const [id, m] of marcadoresViatura.current) {
      if (!vistos.has(id)) { m.remove(); marcadoresViatura.current.delete(id); }
    }
  }, [viaturas]);

  // Sincroniza marcadores de ocorrências.
  useEffect(() => {
    const L = leafletRef.current;
    const mapa = mapaRef.current;
    if (!L || !mapa) return;

    const vistos = new Set<string>();
    for (const o of ocorrencias) {
      if (!o.coordenada) continue;
      vistos.add(o.id);
      const selecionada = o.id === ocorrenciaSelecionadaId;
      const cor = o.status === "EM_ATENDIMENTO" ? "#0369a1" : "#dc2626";
      const icone = L.divIcon({
        className: "",
        html: `<div style="width:${selecionada ? 22 : 16}px;height:${selecionada ? 22 : 16}px;background:${cor};border:2px solid #fff;border-radius:3px;box-shadow:0 0 0 ${selecionada ? 4 : 0}px rgba(220,38,38,.35);transform:rotate(45deg)"></div>`,
        iconSize: [22, 22], iconAnchor: [11, 11],
      });

      let m = marcadoresOcorrencia.current.get(o.id);
      if (!m) {
        m = L.marker([o.coordenada.latitude, o.coordenada.longitude], { icon: icone })
          .bindTooltip(`${o.protocolo} · ${o.tipificacao}`, { direction: "top", offset: [0, -10] })
          .on("click", () => callbacks.current.onSelecionarOcorrencia(o.id))
          .addTo(mapa);
        marcadoresOcorrencia.current.set(o.id, m);
      } else {
        m.setIcon(icone);
      }
    }
    for (const [id, m] of marcadoresOcorrencia.current) {
      if (!vistos.has(id)) { m.remove(); marcadoresOcorrencia.current.delete(id); }
    }
  }, [ocorrencias, ocorrenciaSelecionadaId]);

  return <div ref={divRef} className="mapa" role="application" aria-label="Mapa tático" />;
}
