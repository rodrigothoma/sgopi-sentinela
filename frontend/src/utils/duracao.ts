const SEGUNDOS_POR_MINUTO = 60;
const SEGUNDOS_POR_HORA = 3600;

/** "45 s", "12 min", "1 h 20 min" — duração média legível; ``null`` (sem amostras) vira "—". */
export function formatarDuracao(segundos: number | null): string {
  if (segundos === null) return '—';
  if (segundos < SEGUNDOS_POR_MINUTO) return `${Math.round(segundos)} s`;
  if (segundos < SEGUNDOS_POR_HORA) return `${Math.round(segundos / SEGUNDOS_POR_MINUTO)} min`;
  const horas = Math.floor(segundos / SEGUNDOS_POR_HORA);
  const minutos = Math.round((segundos % SEGUNDOS_POR_HORA) / SEGUNDOS_POR_MINUTO);
  return minutos ? `${horas} h ${minutos} min` : `${horas} h`;
}
