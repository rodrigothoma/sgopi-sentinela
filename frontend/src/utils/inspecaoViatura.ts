import type { Viatura } from '../types/api';

/** Uma posição incompleta ou inválida não pode ser usada para mover a câmera do mapa. */
export function posicaoDaViatura(viatura: Viatura): [number, number] | null {
  const { latitude, longitude } = viatura;
  if (latitude === null || longitude === null || !Number.isFinite(latitude) || !Number.isFinite(longitude)) return null;
  if (Math.abs(latitude) > 90 || Math.abs(longitude) > 180) return null;
  return [latitude, longitude];
}
