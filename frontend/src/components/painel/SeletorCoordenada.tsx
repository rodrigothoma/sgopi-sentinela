import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { CENTRO_PADRAO, corrigirIconesLeaflet } from './leaflet';

interface Props { latitude: number | null; longitude: number | null; onChange: (lat: number, lon: number) => void }

/** Mapa pequeno para clicar/arrastar a coordenada do fato (DEC-03) + campos numéricos. */
export const SeletorCoordenada: React.FC<Props> = ({ latitude, longitude, onChange }) => {
  const divRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const markerRef = useRef<L.Marker | null>(null);

  useEffect(() => {
    if (!divRef.current || mapRef.current) return;
    corrigirIconesLeaflet();
    const map = L.map(divRef.current).setView([latitude ?? CENTRO_PADRAO[0], longitude ?? CENTRO_PADRAO[1]], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '© OpenStreetMap' }).addTo(map);
    map.on('click', (e: L.LeafletMouseEvent) => onChange(Number(e.latlng.lat.toFixed(6)), Number(e.latlng.lng.toFixed(6))));
    mapRef.current = map;
    return () => {
      map.remove();
      mapRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    if (latitude === null || longitude === null) {
      markerRef.current?.remove();
      markerRef.current = null;
      return;
    }
    if (!markerRef.current) {
      markerRef.current = L.marker([latitude, longitude], { draggable: true }).addTo(map);
      markerRef.current.on('dragend', () => {
        const p = markerRef.current!.getLatLng();
        onChange(Number(p.lat.toFixed(6)), Number(p.lng.toFixed(6)));
      });
    } else {
      markerRef.current.setLatLng([latitude, longitude]);
    }
  }, [latitude, longitude, onChange]);

  return (
    <div className="seletor-coordenada">
      <div ref={divRef} className="mapa mapa-pequeno" />
      <div className="grid2">
        <label>
          Latitude
          <input type="number" step="0.000001" min={-90} max={90} value={latitude ?? ''} onChange={(e) => onChange(Number(e.target.value), longitude ?? CENTRO_PADRAO[1])} />
        </label>
        <label>
          Longitude
          <input type="number" step="0.000001" min={-180} max={180} value={longitude ?? ''} onChange={(e) => onChange(latitude ?? CENTRO_PADRAO[0], Number(e.target.value))} />
        </label>
      </div>
    </div>
  );
};
