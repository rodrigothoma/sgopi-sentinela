import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import type { OcorrenciaResumo, OrdemDespacho, Viatura } from '../../types/api';
import {
  CENTRO_PADRAO,
  corrigirIconesLeaflet,
  iconeOcorrencia,
  iconeViatura,
  iconeAlvoDespacho,
  iconePinTatico,
} from './leaflet';

interface Props {
  viaturas: Viatura[];
  ocorrencias: OcorrenciaResumo[];
  selecionada: string | null;
  onSelecionarOcorrencia: (id: string) => void;
  /** Ordens ativas: desenha o trajeto viatura → ocorrência enquanto ela está EM_DESLOCAMENTO. */
  ordens?: OrdemDespacho[];
  pontoTatico?: { latitude: number; longitude: number } | null;
  onCliqueMapa?: (lat: number, lon: number) => void;
}

/** Mapa Leaflet/OSM com marcadores atualizados incrementalmente e pin tático interativo. */
export const MapaTatico: React.FC<Props> = ({
  viaturas,
  ocorrencias,
  selecionada,
  onSelecionarOcorrencia,
  ordens = [],
  pontoTatico: pontoExterno,
  onCliqueMapa,
}) => {
  const divRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const viaturasRef = useRef<Map<string, L.Marker>>(new Map());
  const ocorrenciasRef = useRef<Map<string, L.Marker>>(new Map());
  const alvoRef = useRef<L.Marker | null>(null);
  const pontoTaticoRef = useRef<L.Marker | null>(null);
  const rotasRef = useRef<Map<string, L.Polyline>>(new Map());
  const selecionarRef = useRef(onSelecionarOcorrencia);
  const cliqueRef = useRef(onCliqueMapa);

  const [pontoInterno, setPontoInterno] = useState<{ latitude: number; longitude: number } | null>(null);

  selecionarRef.current = onSelecionarOcorrencia;
  cliqueRef.current = onCliqueMapa;

  const pontoAtual = pontoExterno ?? pontoInterno;

  useEffect(() => {
    if (!divRef.current || mapRef.current) return;
    corrigirIconesLeaflet();
    const map = L.map(divRef.current, {
      zoomControl: true,
      attributionControl: true,
    }).setView(CENTRO_PADRAO, 13);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
      maxZoom: 19,
    }).addTo(map);

    map.on('click', (e: L.LeafletMouseEvent) => {
      const lat = Number(e.latlng.lat.toFixed(6));
      const lng = Number(e.latlng.lng.toFixed(6));
      setPontoInterno({ latitude: lat, longitude: lng });
      cliqueRef.current?.(lat, lng);
    });

    mapRef.current = map;
    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Marcadores de Viaturas
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
        m.bindTooltip(`${v.prefixo} · ${v.placa}`);
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

  // Marcadores de Ocorrências
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
        existente.setZIndexOffset(o.ocorrencia_id === selecionada ? 1000 : 0);
      } else {
        const m = L.marker([o.latitude, o.longitude], { icon: icone }).addTo(map);
        m.bindTooltip(`${o.numero_protocolo} · ${o.natureza}`);
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

    // Alvo de despacho na ocorrência selecionada
    const oSel = ocorrencias.find((x) => x.ocorrencia_id === selecionada);
    if (oSel && oSel.latitude !== null && oSel.longitude !== null) {
      if (!alvoRef.current) {
        alvoRef.current = L.marker([oSel.latitude, oSel.longitude], {
          icon: iconeAlvoDespacho(),
          interactive: false,
          zIndexOffset: 2000,
        }).addTo(map);
      } else {
        alvoRef.current.setLatLng([oSel.latitude, oSel.longitude]);
      }
    } else {
      alvoRef.current?.remove();
      alvoRef.current = null;
    }
  }, [ocorrencias, selecionada]);

  // Pin tático visual para clique manual
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    if (!pontoAtual) {
      pontoTaticoRef.current?.remove();
      pontoTaticoRef.current = null;
      return;
    }

    if (!pontoTaticoRef.current) {
      const pin = L.marker([pontoAtual.latitude, pontoAtual.longitude], {
        icon: iconePinTatico('Ponto Marcado'),
        zIndexOffset: 2500,
      }).addTo(map);

      pin.bindTooltip(`Ponto Tático: ${pontoAtual.latitude.toFixed(5)}, ${pontoAtual.longitude.toFixed(5)}`, {
        direction: 'top',
        offset: [0, -38],
      });

      pontoTaticoRef.current = pin;
    } else {
      pontoTaticoRef.current
        .setLatLng([pontoAtual.latitude, pontoAtual.longitude])
        .setTooltipContent(`Ponto Tático: ${pontoAtual.latitude.toFixed(5)}, ${pontoAtual.longitude.toFixed(5)}`);
    }
  }, [pontoAtual]);

  // Trajeto tracejado da viatura despachada até a ocorrência
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
    const o = ocorrencias.find((x) => x.ocorrencia_id === selecionada);
    if (map && o) map.panTo([o.latitude, o.longitude]);
  }, [selecionada, ocorrencias]);

  return <div ref={divRef} className="mapa mapa-grande" style={{ cursor: 'crosshair' }} />;
};

export default MapaTatico;
