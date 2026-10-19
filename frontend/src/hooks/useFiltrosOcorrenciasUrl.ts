import { useCallback, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import type { FiltrosOcorrencias } from '../types/api';
import { escreverFiltrosNaUrl, lerFiltrosDaUrl } from '../utils/filtrosOcorrencias';

/** Filtros da listagem guardados na query string: o link da página reproduz a mesma busca. */
export function useFiltrosOcorrenciasUrl(): [FiltrosOcorrencias, (filtros: FiltrosOcorrencias) => void] {
  const [searchParams, setSearchParams] = useSearchParams();
  // A string serializada é a identidade estável: o objeto só muda quando a busca muda de fato
  const chave = searchParams.toString();
  const filtros = useMemo(() => lerFiltrosDaUrl(new URLSearchParams(chave)), [chave]);
  const aplicar = useCallback(
    (novos: FiltrosOcorrencias) => setSearchParams((atual) => escreverFiltrosNaUrl(atual, novos), { replace: true }),
    [setSearchParams],
  );
  return [filtros, aplicar];
}
