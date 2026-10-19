import L from 'leaflet';
import iconUrl from 'leaflet/dist/images/marker-icon.png';
import iconRetinaUrl from 'leaflet/dist/images/marker-icon-2x.png';
import shadowUrl from 'leaflet/dist/images/marker-shadow.png';
import { escaparHtml } from '../../utils/html';

/** Alegrete/RS — mesmo centro do simulador. */
export const CENTRO_PADRAO: [number, number] = [-29.7833, -55.7919];

let corrigido = false;
export function corrigirIconesLeaflet(): void {
  if (corrigido) return;
  L.Icon.Default.mergeOptions({ iconUrl, iconRetinaUrl, shadowUrl });
  corrigido = true;
}

const CORES: Record<string, string> = {
  DISPONIVEL: '#16a34a', EM_DESLOCAMENTO: '#2563eb', OPERANDO: '#7c3aed', INDISPONIVEL: '#6b7280',
  SEM_SINAL: '#f59e0b', VALIDADA: '#dc2626', EM_ATENDIMENTO: '#ea580c',
};

export function iconeViatura(situacao: string, sinal: string, prefixo: string): L.DivIcon {
  const cor = sinal === 'SEM_SINAL' ? CORES.SEM_SINAL : CORES[situacao] ?? '#111';
  return L.divIcon({
    className: 'marker-viatura',
    html: `<div class="marker-viatura-inner" style="background:${cor}">🚓<span>${escaparHtml(prefixo)}</span></div>`,
    iconSize: [64, 28],
    iconAnchor: [32, 14],
  });
}

export function iconeOcorrencia(status: string, protocolo: string): L.DivIcon {
  return L.divIcon({
    className: 'marker-ocorrencia',
    html: `<div class="marker-ocorrencia-inner" style="background:${CORES[status] ?? '#dc2626'}">⚠<span>${escaparHtml(protocolo.slice(-6))}</span></div>`,
    iconSize: [72, 28],
    iconAnchor: [36, 28],
  });
}

/** Pin em SVG vetorial estilizado em gota com ponto de precisão e anel de pulso para seleção de local do fato. */
export function iconePinFato(rotulo?: string): L.DivIcon {
  return L.divIcon({
    className: 'marker-pin-custom',
    html: `
      <div class="sgopi-pin-wrap">
        <div class="sgopi-pin-pulse"></div>
        <svg class="sgopi-pin-svg" width="36" height="46" viewBox="0 0 36 46" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M18 2C9.163 2 2 9.163 2 18C2 28.5 16.2 39.5 17.2 40.2C17.7 40.6 18.3 40.6 18.8 40.2C19.8 39.5 34 28.5 34 18C34 9.163 26.837 2 18 2Z" fill="#dc2626" stroke="#ffffff" stroke-width="2.5"/>
          <circle cx="18" cy="18" r="6.5" fill="#ffffff"/>
          <circle cx="18" cy="18" r="3.5" fill="#b91c1c"/>
        </svg>
        ${rotulo ? `<span class="sgopi-pin-badge">${escaparHtml(rotulo)}</span>` : ''}
      </div>
    `,
    iconSize: [36, 46],
    iconAnchor: [18, 42],
  });
}

/** Marcador de mira tática em SVG para destino de despacho ou ocorrência em foco. */
export function iconeAlvoDespacho(): L.DivIcon {
  return L.divIcon({
    className: 'marker-alvo-custom',
    html: `
      <div class="sgopi-alvo-wrap">
        <div class="sgopi-alvo-radar"></div>
        <svg class="sgopi-alvo-svg" width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="20" cy="20" r="15" stroke="#2563eb" stroke-width="2.5" stroke-dasharray="4 2" fill="rgba(37, 99, 235, 0.22)"/>
          <circle cx="20" cy="20" r="5" fill="#2563eb"/>
          <line x1="20" y1="0" x2="20" y2="8" stroke="#2563eb" stroke-width="2.5"/>
          <line x1="20" y1="32" x2="20" y2="40" stroke="#2563eb" stroke-width="2.5"/>
          <line x1="0" y1="20" x2="8" y2="20" stroke="#2563eb" stroke-width="2.5"/>
          <line x1="32" y1="20" x2="40" y2="20" stroke="#2563eb" stroke-width="2.5"/>
        </svg>
      </div>
    `,
    iconSize: [40, 40],
    iconAnchor: [20, 20],
  });
}

/** Pin tático azul/âmbar para cliques manuais do despachador/operador no mapa. */
export function iconePinTatico(rotulo?: string): L.DivIcon {
  return L.divIcon({
    className: 'marker-pin-custom',
    html: `
      <div class="sgopi-pin-wrap">
        <div class="sgopi-pin-pulse" style="background: rgba(37, 99, 235, 0.45);"></div>
        <svg class="sgopi-pin-svg" width="36" height="46" viewBox="0 0 36 46" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M18 2C9.163 2 2 9.163 2 18C2 28.5 16.2 39.5 17.2 40.2C17.7 40.6 18.3 40.6 18.8 40.2C19.8 39.5 34 28.5 34 18C34 9.163 26.837 2 18 2Z" fill="#2563eb" stroke="#ffffff" stroke-width="2.5"/>
          <circle cx="18" cy="18" r="6.5" fill="#ffffff"/>
          <circle cx="18" cy="18" r="3.5" fill="#1d4ed8"/>
        </svg>
        ${rotulo ? `<span class="sgopi-pin-badge" style="background: #2563eb;">${escaparHtml(rotulo)}</span>` : ''}
      </div>
    `,
    iconSize: [36, 46],
    iconAnchor: [18, 42],
  });
}

