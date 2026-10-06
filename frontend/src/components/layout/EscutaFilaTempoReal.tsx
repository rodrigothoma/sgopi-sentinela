import React, { useCallback } from 'react';
import { useTempoReal } from '../../hooks/useTempoReal';
import type { EventoTempoReal } from '../../types/api';

/** Eventos que alteram a quantidade de ocorrências aguardando revisão. */
const EVENTOS_DA_FILA = new Set([
  'OcorrenciaValidada',
  'OcorrenciaDevolvida',
  'OcorrenciaRejeitada',
  'OcorrenciaReenviada',
  'OcorrenciaArquivada',
  'OcorrenciaExcluida',
]);

/**
 * Mantém o contador da fila em tempo real.
 *
 * Não renderiza nada: existe só para assinar o canal e avisar o menu. Fica num
 * componente próprio, montado apenas para quem vê a fila, para que os demais
 * papéis não abram uma conexão WebSocket sem necessidade.
 */
export const EscutaFilaTempoReal: React.FC<{ onMudou: () => void }> = ({ onMudou }) => {
  const aoEvento = useCallback(
    (e: EventoTempoReal) => {
      if (EVENTOS_DA_FILA.has(e.tipo)) onMudou();
    },
    [onMudou],
  );

  // Ao reconectar, pode ter havido mudança durante a queda: recarrega.
  useTempoReal(aoEvento, onMudou);
  return null;
};

export default EscutaFilaTempoReal;
