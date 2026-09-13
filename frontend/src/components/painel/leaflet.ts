import L from 'leaflet';
import iconUrl from 'leaflet/dist/images/marker-icon.png';
import iconRetinaUrl from 'leaflet/dist/images/marker-icon-2x.png';
import shadowUrl from 'leaflet/dist/images/marker-shadow.png';

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
    html: `<div class="marker-viatura-inner" style="background:${cor}">🚓<span>${prefixo}</span></div>`,
    iconSize: [64, 28],
    iconAnchor: [32, 14],
  });
}

export function iconeOcorrencia(status: string, protocolo: string): L.DivIcon {
  return L.divIcon({
    className: 'marker-ocorrencia',
    html: `<div class="marker-ocorrencia-inner" style="background:${CORES[status] ?? '#dc2626'}">⚠<span>${protocolo.slice(-6)}</span></div>`,
    iconSize: [72, 28],
    iconAnchor: [36, 28],
  });
}
