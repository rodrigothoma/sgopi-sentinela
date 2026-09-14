import { useEffect, useRef, useState } from 'react';
import { ClienteTempoReal, type EstadoConexao } from '../services/tempoRealService';
import type { EventoTempoReal } from '../types/api';

/** Assina o canal de tempo real; `onEvento` e `onReconectar` são lidos por ref para não reabrir a conexão. */
export function useTempoReal(onEvento: (e: EventoTempoReal) => void, onReconectar: () => void): EstadoConexao {
  const [estado, setEstado] = useState<EstadoConexao>('conectando');
  const eventoRef = useRef(onEvento);
  const reconectarRef = useRef(onReconectar);
  eventoRef.current = onEvento;
  reconectarRef.current = onReconectar;

  useEffect(() => {
    const cliente = new ClienteTempoReal((e) => eventoRef.current(e), setEstado, () => reconectarRef.current());
    cliente.conectar();
    return () => cliente.fechar();
  }, []);

  return estado;
}
