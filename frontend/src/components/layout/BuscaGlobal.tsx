import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../hooks/useAuth';
import { ocorrenciasService } from '../../services/ocorrenciasService';
import { formatarNatureza } from '../../utils/formatarNatureza';
import {
  MAXIMO_CANDIDATOS_TERMO,
  MAXIMO_RESULTADOS_BUSCA,
  intersectarResultados,
  mesclarResultadosBusca,
  separarTermos,
  termoBuscavel,
} from '../../utils/buscaOcorrencias';
import type { FiltrosOcorrencias, OcorrenciaResumo } from '../../types/api';

const ATRASO_BUSCA_MS = 300;

/** Uma consulta por campo, porque os filtros da API combinam com E. */
const CAMPOS_BUSCADOS: (keyof Pick<FiltrosOcorrencias, 'protocolo' | 'natureza' | 'texto'>)[] = [
  'protocolo',
  'natureza',
  'texto',
];

/**
 * Tudo que casa com um termo, em qualquer um dos campos.
 *
 * Sem teto na união: o corte final é da interseção entre os termos, depois de
 * saber quem sobreviveu a todos.
 */
function acharPorTermo(palavra: string, limite: number): Promise<OcorrenciaResumo[]> {
  return Promise.all(
    CAMPOS_BUSCADOS.map((campo) =>
      ocorrenciasService
        .listar([], limite, 0, true, { [campo]: palavra })
        .then((pagina) => pagina.itens)
        // Uma consulta que falha não derruba as outras.
        .catch(() => [] as OcorrenciaResumo[]),
    ),
  ).then((listas) => mesclarResultadosBusca(listas, Number.POSITIVE_INFINITY));
}

/**
 * Busca global de ocorrências (protocolo, natureza ou endereço).
 *
 * Não havia busca em nenhuma tela: para achar um protocolo era preciso saber em
 * qual módulo ele estava. A filtragem é do servidor — filtrar no cliente
 * limitaria o resultado à página baixada. Cada palavra digitada estreita o
 * resultado: "roubo andradas" devolve o roubo daquela rua, não os dois
 * conjuntos somados. O item abre o registro pela rota que já aceita
 * ``?ocorrencia=<id>``.
 */
export const BuscaGlobal: React.FC<{ onNavegar?: () => void }> = ({ onNavegar }) => {
  const { t } = useTranslation('common');
  const { tem } = useAuth();
  const navigate = useNavigate();

  const [termo, setTermo] = useState('');
  const [resultados, setResultados] = useState<OcorrenciaResumo[]>([]);
  const [buscando, setBuscando] = useState(false);
  const [aberto, setAberto] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Quem revisa cai na fila; o agente vê as próprias ocorrências.
  const destino = tem('DELEGADO', 'SUPERVISOR') ? '/fila' : '/minhas';

  useEffect(() => {
    if (!termoBuscavel(termo)) {
      setResultados([]);
      setBuscando(false);
      return;
    }

    let ativo = true;
    setBuscando(true);
    const id = window.setTimeout(() => {
      const termos = separarTermos(termo);
      // Com vários termos o cruzamento é local, e 6 por campo esconderia quem casa com todos.
      const limite = termos.length > 1 ? MAXIMO_CANDIDATOS_TERMO : MAXIMO_RESULTADOS_BUSCA;

      Promise.all(termos.map((palavra) => acharPorTermo(palavra, limite)))
        .then((porTermo) => {
          if (!ativo) return;
          setResultados(intersectarResultados(porTermo));
          setAberto(true);
        })
        .finally(() => { if (ativo) setBuscando(false); });
    }, ATRASO_BUSCA_MS);

    return () => { ativo = false; window.clearTimeout(id); };
  }, [termo]);

  // Fecha ao clicar fora, para o resultado não ficar preso sobre a navegação.
  useEffect(() => {
    const aoClicar = (ev: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(ev.target as Node)) setAberto(false);
    };
    document.addEventListener('mousedown', aoClicar);
    return () => document.removeEventListener('mousedown', aoClicar);
  }, []);

  const abrir = (o: OcorrenciaResumo) => {
    setAberto(false);
    setTermo('');
    onNavegar?.();
    navigate(`${destino}?ocorrencia=${o.ocorrencia_id}`);
  };

  return (
    <div className="busca-global" ref={containerRef}>
      <input
        type="search"
        className="busca-global-input"
        data-cy="busca-global"
        value={termo}
        onChange={(e) => setTermo(e.target.value)}
        onFocus={() => resultados.length > 0 && setAberto(true)}
        placeholder={t('busca.placeholder', { defaultValue: 'Buscar protocolo, natureza…' })}
        aria-label={t('busca.rotulo', { defaultValue: 'Busca global de ocorrências' })}
      />

      {aberto && (
        <div className="busca-global-resultados" role="listbox">
          {buscando && <div className="busca-global-vazio">{t('busca.buscando', { defaultValue: 'Buscando…' })}</div>}
          {!buscando && resultados.length === 0 && (
            <div className="busca-global-vazio">{t('busca.vazio', { defaultValue: 'Nada encontrado' })}</div>
          )}
          {resultados.map((o) => (
            <button
              key={o.ocorrencia_id}
              type="button"
              className="busca-global-item"
              data-cy="busca-global-item"
              onClick={() => abrir(o)}
              role="option"
            >
              <strong>{o.numero_protocolo}</strong>
              <span className="busca-global-detalhe">
                {formatarNatureza(o.natureza, t)} · {o.localizacao}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default BuscaGlobal;
