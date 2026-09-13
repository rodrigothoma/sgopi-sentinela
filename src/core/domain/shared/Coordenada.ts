import { ErroValidacao } from "./DomainError";

/** Objeto de valor imutável para um ponto geográfico (WGS-84). */
export interface Coordenada {
  readonly latitude: number;
  readonly longitude: number;
}

export function criarCoordenada(latitude: number, longitude: number): Coordenada {
  if (!Number.isFinite(latitude) || latitude < -90 || latitude > 90) {
    throw new ErroValidacao("Latitude inválida.", { latitude });
  }
  if (!Number.isFinite(longitude) || longitude < -180 || longitude > 180) {
    throw new ErroValidacao("Longitude inválida.", { longitude });
  }
  return Object.freeze({ latitude, longitude });
}

const RAIO_TERRA_KM = 6371.0088;

/**
 * Distância geodésica (Haversine) em quilômetros — UC02 passo 4.
 * Função pura, sem dependências externas (RNF05).
 */
export function distanciaHaversineKm(a: Coordenada, b: Coordenada): number {
  const paraRad = (g: number) => (g * Math.PI) / 180;
  const dLat = paraRad(b.latitude - a.latitude);
  const dLon = paraRad(b.longitude - a.longitude);
  const lat1 = paraRad(a.latitude);
  const lat2 = paraRad(b.latitude);

  const h =
    Math.sin(dLat / 2) ** 2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLon / 2) ** 2;
  return 2 * RAIO_TERRA_KM * Math.asin(Math.min(1, Math.sqrt(h)));
}
