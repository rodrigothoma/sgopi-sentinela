import { useEffect, useState } from 'react';

const UM_MINUTO_MS = 60_000;

/**
 * Relógio compartilhado por todos os assinantes, com um único ``setInterval``
 * no módulo.
 *
 * Telas que mostram tempo decorrido linha a linha criariam um temporizador por
 * linha, todos acordando para fazer a mesma conta. Aqui o intervalo existe
 * enquanto houver pelo menos um assinante e é desligado quando o último sai.
 */
let intervalo: number | null = null;
const assinantes = new Set<(agora: number) => void>();

function assinar(ouvinte: (agora: number) => void): () => void {
  assinantes.add(ouvinte);
  if (intervalo === null) {
    intervalo = window.setInterval(() => {
      const agora = Date.now();
      assinantes.forEach((a) => a(agora));
    }, UM_MINUTO_MS);
  }
  return () => {
    assinantes.delete(ouvinte);
    if (assinantes.size === 0 && intervalo !== null) {
      window.clearInterval(intervalo);
      intervalo = null;
    }
  };
}

/** Instante atual, atualizado a cada minuto. */
export function useRelogioMinuto(): number {
  const [agora, setAgora] = useState(() => Date.now());
  useEffect(() => assinar(setAgora), []);
  return agora;
}
