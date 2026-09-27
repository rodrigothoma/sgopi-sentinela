import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { CENTRO_PADRAO, corrigirIconesLeaflet, iconePinFato } from './leaflet';

interface Props {
  latitude: number | null;
  longitude: number | null;
  onChange: (lat: number, lon: number) => void;
}

/** Mapa interativo para clicar e arrastar o pin de coordenada do fato (DEC-03) + campos numéricos. */
export const SeletorCoordenada: React.FC<Props> = ({ latitude, longitude, onChange }) => {
  const divRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const markerRef = useRef<L.Marker | null>(null);

  const onChangeRef = useRef(onChange);
  onChangeRef.current = onChange;

  useEffect(() => {
    if (!divRef.current || mapRef.current) return;
    corrigirIconesLeaflet();
    const centroInicial: [number, number] = [
      latitude ?? CENTRO_PADRAO[0],
      longitude ?? CENTRO_PADRAO[1],
    ];
    const map = L.map(divRef.current, {
      zoomControl: true,
      attributionControl: true,
    }).setView(centroInicial, 14);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
      maxZoom: 19,
    }).addTo(map);

    map.on('click', (e: L.LeafletMouseEvent) => {
      const lat = Number(e.latlng.lat.toFixed(6));
      const lng = Number(e.latlng.lng.toFixed(6));
      onChangeRef.current(lat, lng);
      map.panTo([lat, lng]);
    });

    const timer = setTimeout(() => {
      map.invalidateSize();
    }, 150);

    mapRef.current = map;
    return () => {
      clearTimeout(timer);
      if (markerRef.current) {
        markerRef.current.remove();
        markerRef.current = null;
      }
      map.remove();
      mapRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    if (latitude === null || longitude === null) {
      if (markerRef.current) {
        markerRef.current.remove();
        markerRef.current = null;
      }
      return;
    }

    if (!markerRef.current || !map.hasLayer(markerRef.current)) {
      if (markerRef.current) {
        markerRef.current.remove();
      }
      const pin = L.marker([latitude, longitude], {
        draggable: true,
        icon: iconePinFato('Local do Fato'),
        zIndexOffset: 1500,
      }).addTo(map);

      pin.bindTooltip(`Local do fato: ${latitude.toFixed(5)}, ${longitude.toFixed(5)}`, {
        direction: 'top',
        offset: [0, -38],
      });

      pin.on('dragend', () => {
        const p = pin.getLatLng();
        onChangeRef.current(Number(p.lat.toFixed(6)), Number(p.lng.toFixed(6)));
      });

      markerRef.current = pin;
    } else {
      markerRef.current
        .setLatLng([latitude, longitude])
        .setIcon(iconePinFato('Local do Fato'))
        .setTooltipContent(`Local do fato: ${latitude.toFixed(5)}, ${longitude.toFixed(5)}`);
    }
  }, [latitude, longitude]);

  return (
    <div className="seletor-coordenada">
      <div
        ref={divRef}
        className="mapa mapa-pequeno"
        style={{ height: '300px', cursor: 'crosshair', position: 'relative' }}
      />
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', margin: '4px 0 8px', fontSize: '0.8rem', color: 'var(--muted)' }}>
        <span>📍 Clique no mapa para marcar o pin do local do fato (ou arraste o pin).</span>
        {latitude !== null && longitude !== null && (
          <span style={{ color: 'var(--primary)', fontWeight: 600 }}>
            {latitude.toFixed(5)}, {longitude.toFixed(5)}
          </span>
        )}
      </div>
      <div className="grid2">
        <label>
          Latitude
          <input
            type="number"
            step="0.000001"
            min={-90}
            max={90}
            value={latitude ?? ''}
            onChange={(e) => onChange(Number(e.target.value), longitude ?? CENTRO_PADRAO[1])}
            style={{ height: '42px' }}
          />
        </label>
        <label>
          Longitude
          <input
            type="number"
            step="0.000001"
            min={-180}
            max={180}
            value={longitude ?? ''}
            onChange={(e) => onChange(latitude ?? CENTRO_PADRAO[0], Number(e.target.value))}
            style={{ height: '42px' }}
          />
        </label>
      </div>
    </div>
  );
};
export default SeletorCoordenada;
