import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../hooks/useAuth';
import { ocorrenciasService } from '../../services/ocorrenciasService';
import { formatarNatureza } from '../../utils/formatarNatureza';
import type { OcorrenciaResumo } from '../../types/api';

const ATRASO_BUSCA_MS = 300;
const MINIMO_CARACTERES = 2;
const MAXIMO_RESULTADOS = 6;
/** Teto de leitura por consulta; a filtragem fina acontece no cliente. */
const LIMITE_CONSULTA = 200;

const normalizar = (v: string): string =>
  v.normalize('NFKD').replace(/[̀-ͯ]/g, '').toLowerCase().trim();

/**
 * Busca global de ocorrências (protocolo, natureza ou endereço).
 *
 * Não havia busca em nenhuma tela: para achar um protocolo era preciso saber em
 * qual módulo ele estava. O resultado abre o registro pela rota que já aceita
 * ``?ocorrencia=<id>``, reaproveitando o deep link existente.
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
    const alvo = normalizar(termo);
    if (alvo.length < MINIMO_CARACTERES) {
      setResultados([]);
      setBuscando(false);
      return;
    }

    let ativo = true;
    setBuscando(true);
    const id = window.setTimeout(() => {
      ocorrenciasService
        .listar([], LIMITE_CONSULTA, 0, true)
        .then((pagina) => {
          if (!ativo) return;
          const achados = pagina.itens.filter((o) =>
            [o.numero_protocolo, o.natureza, o.localizacao].some((campo) => normalizar(campo ?? '').includes(alvo)),
          );
          setResultados(achados.slice(0, MAXIMO_RESULTADOS));
          setAberto(true);
        })
        .catch(() => { if (ativo) setResultados([]); })
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
            <button key={o.ocorrencia_id} type="button" className="busca-global-item" onClick={() => abrir(o)} role="option">
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
