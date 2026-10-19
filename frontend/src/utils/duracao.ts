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

/**
 * Tempo decorrido de uma espera em aberto — igual a ``formatarDuracao`` abaixo de
 * 24 h e em dias acima disso ("2 d 4 h"), porque "há 52 h" não se lê de imediato.
 *
 * Separada de ``formatarDuracao`` de propósito: aquela formata médias dos
 * indicadores, onde a granularidade em horas é a desejada.
 */
export function formatarEspera(segundos: number): string {
  // Arredonda uma única vez, em minutos, e propaga o excedente para hora e dia:
  // evita resultados como "23 h 60 min" na virada de cada unidade.
  const totalMinutos = Math.round(segundos / SEGUNDOS_POR_MINUTO);
  if (totalMinutos < 60) return formatarDuracao(segundos);

  const totalHoras = Math.floor(totalMinutos / 60);
  const minutos = totalMinutos % 60;
  if (totalHoras < 24) return minutos ? `${totalHoras} h ${minutos} min` : `${totalHoras} h`;

  const dias = Math.floor(totalHoras / 24);
  const horas = totalHoras % 24;
  return horas ? `${dias} d ${horas} h` : `${dias} d`;
}
