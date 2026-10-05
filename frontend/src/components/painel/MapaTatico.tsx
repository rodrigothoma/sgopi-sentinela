import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet.heat';
import type { OcorrenciaResumo, OrdemDespacho, Viatura } from '../../types/api';
import type { PontoCalor } from '../../utils/manchas';
import type { AreaRisco } from '../../services/inteligenciaService';
import { CENTRO_PADRAO, corrigirIconesLeaflet, iconeOcorrencia, iconeViatura } from './leaflet';
import { escaparHtml } from '../../utils/html';
import i18n from '../../i18n';

/** Rótulo do marcador: protocolo, natureza e, quando houver, a gravidade (sugestão #7). */
function rotuloOcorrencia(o: OcorrenciaResumo): string {
  const prioridade = o.prioridade ? ` · ${i18n.t(`common:prioridade.${o.prioridade}`)}` : '';
  return escaparHtml(`${o.numero_protocolo} · ${o.natureza}${prioridade}`);
}

/** Campo interno do leaflet.heat: redesenho agendado via requestAnimationFrame. */
type HeatLayerInterno = L.HeatLayer & { _frame?: number | null };

/**
 * Remove a camada de calor cancelando antes o redesenho pendente — sem isso o frame agendado
 * roda com `_map` nulo e lança "Cannot read properties of null (reading 'getSize')".
 */
const removerHeat = (camada: L.HeatLayer | null): void => {
  const interna = camada as HeatLayerInterno | null;
  if (interna?._frame) {
    L.Util.cancelAnimFrame(interna._frame);
    interna._frame = null;
  }
  camada?.remove();
};

interface Props {
  viaturas: Viatura[];
  ocorrencias: OcorrenciaResumo[];
  selecionada: string | null;
  onSelecionarOcorrencia: (id: string) => void;
  /** Ordens ativas: desenha o trajeto viatura → ocorrência enquanto ela está EM_DESLOCAMENTO. */
  ordens?: OrdemDespacho[];
  heatAtivo: boolean;
  pontosCalor: PontoCalor[];
  areasRisco?: AreaRisco[];
}

/** Mapa Leaflet/OSM com marcadores atualizados incrementalmente (sem recriar o mapa a cada evento). */
export const MapaTatico: React.FC<Props> = ({
  viaturas,
  ocorrencias,
  selecionada,
  onSelecionarOcorrencia,
  ordens = [],
  heatAtivo,
  pontosCalor,
  areasRisco = [],
}) => {
  const divRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const viaturasRef = useRef<Map<string, L.Marker>>(new Map());
  const ocorrenciasRef = useRef<Map<string, L.Marker>>(new Map());
  const rotasRef = useRef<Map<string, L.Polyline>>(new Map());
  const areasRef = useRef<Map<string, L.Circle>>(new Map());
  const heatRef = useRef<L.HeatLayer | null>(null);
  const selecionarRef = useRef(onSelecionarOcorrencia);
  selecionarRef.current = onSelecionarOcorrencia;

  useEffect(() => {
    if (!divRef.current || mapRef.current) return;
    corrigirIconesLeaflet();
    const map = L.map(divRef.current).setView(CENTRO_PADRAO, 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '© OpenStreetMap' }).addTo(map);
    mapRef.current = map;
    return () => {
      removerHeat(heatRef.current);
      heatRef.current = null;
      for (const c of areasRef.current.values()) {
        c.remove();
      }
      areasRef.current.clear();
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const vistos = new Set<string>();
    for (const v of viaturas) {
      if (v.latitude === null || v.longitude === null) continue;
      vistos.add(v.id);
      const icone = iconeViatura(v.situacao, v.sinal, v.prefixo);
      const existente = viaturasRef.current.get(v.id);
      if (existente) {
        existente.setLatLng([v.latitude, v.longitude]).setIcon(icone);
      } else {
        const m = L.marker([v.latitude, v.longitude], { icon: icone }).addTo(map);
        m.bindTooltip(escaparHtml(`${v.prefixo} · ${v.placa}`));
        viaturasRef.current.set(v.id, m);
      }
    }
    for (const [id, m] of viaturasRef.current) {
      if (!vistos.has(id)) {
        m.remove();
        viaturasRef.current.delete(id);
      }
    }
  }, [viaturas]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const vistos = new Set<string>();
    for (const o of ocorrencias) {
      vistos.add(o.ocorrencia_id);
      const icone = iconeOcorrencia(o.status, o.numero_protocolo);
      const existente = ocorrenciasRef.current.get(o.ocorrencia_id);
      if (existente) {
        existente.setLatLng([o.latitude, o.longitude]).setIcon(icone);
        existente.setTooltipContent(rotuloOcorrencia(o));
        existente.setZIndexOffset(o.ocorrencia_id === selecionada ? 1000 : o.prioridade === 'URGENTE' ? 500 : 0);
      } else {
        const m = L.marker([o.latitude, o.longitude], { icon: icone }).addTo(map);
        m.bindTooltip(rotuloOcorrencia(o));
        if (o.prioridade === 'URGENTE') m.setZIndexOffset(500);
        m.on('click', () => selecionarRef.current(o.ocorrencia_id));
        ocorrenciasRef.current.set(o.ocorrencia_id, m);
      }
    }
    for (const [id, m] of ocorrenciasRef.current) {
      if (!vistos.has(id)) {
        m.remove();
        ocorrenciasRef.current.delete(id);
      }
    }
  }, [ocorrencias, selecionada]);

  // trajeto tracejado da viatura despachada até a ocorrência (some quando ela chega — OPERANDO)
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const vistos = new Set<string>();
    for (const ordem of ordens) {
      const v = viaturas.find((x) => x.id === ordem.viatura_id);
      const o = ocorrencias.find((x) => x.ocorrencia_id === ordem.ocorrencia_id);
      if (!v || !o || v.situacao !== 'EM_DESLOCAMENTO' || v.latitude === null || v.longitude === null) continue;
      vistos.add(ordem.id);
      const pontos: L.LatLngExpression[] = [[v.latitude, v.longitude], [o.latitude, o.longitude]];
      const existente = rotasRef.current.get(ordem.id);
      if (existente) {
        existente.setLatLngs(pontos);
      } else {
        rotasRef.current.set(ordem.id, L.polyline(pontos, { color: '#2563eb', weight: 3, dashArray: '8 8', opacity: 0.8 }).addTo(map));
      }
    }
    for (const [id, linha] of rotasRef.current) {
      if (!vistos.has(id)) {
        linha.remove();
        rotasRef.current.delete(id);
      }
    }
  }, [ordens, viaturas, ocorrencias]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    if (!heatAtivo || pontosCalor.length === 0) {
      removerHeat(heatRef.current);
      heatRef.current = null;
      return;
    }
    if (heatRef.current) {
      heatRef.current.setLatLngs(pontosCalor);
    } else {
      heatRef.current = L.heatLayer(pontosCalor, { radius: 30, blur: 20, maxZoom: 13 }).addTo(map);
    }
  }, [heatAtivo, pontosCalor]);

  // Áreas de risco / manchas críticas com círculos táticos e popups informativos
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const vistos = new Set<string>();
    for (const a of areasRisco) {
      vistos.add(a.id);
      const cor =
        a.nivel_risco === 'CRITICA'
          ? '#dc2626'
          : a.nivel_risco === 'ALTA'
            ? '#ea580c'
            : a.nivel_risco === 'MEDIA'
              ? '#eab308'
              : '#3b82f6';

      const popupHtml = `
        <div style="font-family: inherit; font-size: 13px; line-height: 1.45; min-width: 190px;">
          <div style="font-weight: 700; margin-bottom: 4px; color: ${cor};">🚨 ${escaparHtml(a.nome)}</div>
          <div><strong>Criticidade:</strong> <span style="color: ${cor}; font-weight: 700;">${escaparHtml(a.nivel_risco)}</span></div>
          <div><strong>Ocorrências:</strong> ${Number(a.total_ocorrencias)} (${Number(a.total_24h)} em 24h)</div>
          <div><strong>Predominantes:</strong> ${escaparHtml(a.naturezas_predominantes.slice(0, 3).join(', '))}</div>
          <div><strong>Raio de Cobertura:</strong> ${Math.round(a.raio_metros)}m</div>
        </div>
      `;

      const existente = areasRef.current.get(a.id);
      if (existente) {
        existente.setLatLng([a.latitude, a.longitude]);
        existente.setRadius(a.raio_metros);
        existente.setStyle({ color: cor, fillColor: cor });
        existente.setPopupContent(popupHtml);
      } else {
        const circulo = L.circle([a.latitude, a.longitude], {
          radius: a.raio_metros,
          color: cor,
          fillColor: cor,
          fillOpacity: a.nivel_risco === 'CRITICA' ? 0.28 : 0.18,
          weight: 2,
          dashArray: a.nivel_risco === 'CRITICA' ? '4 4' : undefined,
        }).addTo(map);
        circulo.bindTooltip(escaparHtml(`${a.nome} [${a.nivel_risco}]`));
        circulo.bindPopup(popupHtml);
        areasRef.current.set(a.id, circulo);
      }
    }
    for (const [id, c] of areasRef.current) {
      if (!vistos.has(id)) {
        c.remove();
        areasRef.current.delete(id);
      }
    }
  }, [areasRisco]);

  useEffect(() => {
    const map = mapRef.current;
    const o = ocorrencias.find((x) => x.ocorrencia_id === selecionada);
    if (map && o) map.panTo([o.latitude, o.longitude]);
  }, [selecionada, ocorrencias]);

  return <div ref={divRef} className="mapa mapa-grande" />;
};
