/**
 * Geocodificação via Nominatim (OpenStreetMap) — mesma origem dos tiles do mapa.
 * Uso leve e opcional: qualquer falha (rede, limite, sem resultado) devolve null e
 * o formulário segue com a coordenada marcada e o endereço digitado pelo usuário.
 */
const BASE = 'https://nominatim.openstreetmap.org';
const TIMEOUT_MS = 6000;

export interface EnderecoGeocodificado { endereco: string; latitude: number; longitude: number }

interface RespostaNominatim {
  display_name?: string;
  lat?: string;
  lon?: string;
  address?: Record<string, string | undefined>;
}

async function consultar(caminho: string, params: Record<string, string>, signal?: AbortSignal): Promise<RespostaNominatim | RespostaNominatim[] | null> {
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), TIMEOUT_MS);
  signal?.addEventListener('abort', () => controller.abort());
  try {
    const url = new URL(`${BASE}/${caminho}`);
    Object.entries({ format: 'jsonv2', 'accept-language': 'pt-BR', ...params }).forEach(([k, v]) => url.searchParams.set(k, v));
    const r = await fetch(url.toString(), { signal: controller.signal, headers: { Accept: 'application/json' } });
    if (!r.ok) return null;
    return (await r.json()) as RespostaNominatim | RespostaNominatim[];
  } catch {
    return null;
  } finally {
    window.clearTimeout(timer);
  }
}

/** Monta "Rua, número — Bairro, Cidade/UF" a partir do detalhamento; cai no display_name. */
function resumirEndereco(r: RespostaNominatim): string | null {
  const a = r.address ?? {};
  const rua = a.road ?? a.pedestrian ?? a.footway ?? a.residential ?? a.neighbourhood;
  const numero = a.house_number;
  const bairro = a.suburb ?? a.neighbourhood ?? a.quarter;
  const cidade = a.city ?? a.town ?? a.village ?? a.municipality;
  const uf = a.state_code ?? a['ISO3166-2-lvl4']?.split('-')[1];
  const partes = [
    [rua, numero].filter(Boolean).join(', '),
    [bairro, [cidade, uf].filter(Boolean).join('/')].filter(Boolean).join(', '),
  ].filter(Boolean);
  if (partes.length) return partes.join(' — ');
  return r.display_name ?? null;
}

export const geocodificacaoService = {
  /** Coordenada → endereço legível (usado ao clicar no mapa). */
  async reverso(latitude: number, longitude: number, signal?: AbortSignal): Promise<string | null> {
    const r = await consultar('reverse', { lat: String(latitude), lon: String(longitude), zoom: '18' }, signal);
    if (!r || Array.isArray(r)) return null;
    return resumirEndereco(r);
  },
  /** Endereço digitado → coordenada (usado no modo "escrever endereço"). */
  async buscar(endereco: string, signal?: AbortSignal): Promise<EnderecoGeocodificado | null> {
    const r = await consultar('search', { q: endereco, limit: '1', countrycodes: 'br', addressdetails: '1' }, signal);
    const item = Array.isArray(r) ? r[0] : null;
    if (!item?.lat || !item.lon) return null;
    return {
      endereco: resumirEndereco(item) ?? endereco,
      latitude: Number(Number(item.lat).toFixed(6)),
      longitude: Number(Number(item.lon).toFixed(6)),
    };
  },
};
