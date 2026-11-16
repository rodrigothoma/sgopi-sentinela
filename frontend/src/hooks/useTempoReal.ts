import { useEffect, useRef, useState } from 'react';
import { assinarTempoReal, type EstadoConexao } from '../services/tempoRealService';
import type { EventoTempoReal } from '../types/api';

interface OuvinteTempoReal {
  onEvento?: (e: EventoTempoReal) => void;
  onReconectar?: () => void;
}

/**
 * Assina o canal de tempo real compartilhado (uma conexão WebSocket por sessão);
 * os callbacks são lidos por ref para não reabrir a conexão a cada render.
 */
export function useTempoRealListener({ onEvento, onReconectar }: OuvinteTempoReal): void {
  const eventoRef = useRef(onEvento);
  const reconectarRef = useRef(onReconectar);
  eventoRef.current = onEvento;
  reconectarRef.current = onReconectar;

  useEffect(() => {
    const ouvinte = (e: EventoTempoReal) => eventoRef.current?.(e);
    const reconectar = () => reconectarRef.current?.();
    return assinarTempoReal(ouvinte, reconectar);
  }, []);
}

/** Como `useTempoRealListener`, mas também expõe o estado da conexão (indicadores de status). */
export function useTempoReal(onEvento: (e: EventoTempoReal) => void, onReconectar: () => void): EstadoConexao {
  const [estado, setEstado] = useState<EstadoConexao>('conectando');
  useTempoRealListener({ onEvento, onReconectar });

  useEffect(() => assinarTempoReal(undefined, undefined, setEstado), []);

  return estado;
}
