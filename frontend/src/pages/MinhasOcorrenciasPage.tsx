import React, { useCallback, useEffect, useState } from 'react';
import { Navigate, useNavigate, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { FiltrosOcorrenciasBar } from '../components/ocorrencias/FiltrosOcorrencias';
import { PrioridadeBadge } from '../components/PrioridadeBadge';
import { StatusBadge } from '../components/StatusBadge';
import { formatarNatureza } from '../utils/formatarNatureza';
import { useFiltrosOcorrenciasUrl } from '../hooks/useFiltrosOcorrenciasUrl';
import { useToast } from '../hooks/useToast';
import { mensagemDeErro } from '../services/api';
import { ocorrenciasService } from '../services/ocorrenciasService';
import type { OcorrenciaResumo } from '../types/api';
import { temFiltroAtivo } from '../utils/filtrosOcorrencias';
import { idOcorrenciaLegada, urlDoDetalhe } from '../utils/ocorrenciaDeepLink';

export const MinhasOcorrenciasPage: React.FC = () => {
  const { t } = useTranslation(['ocorrencias', 'common']);
  const { avisar } = useToast();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const legado = idOcorrenciaLegada(searchParams);
  const [itens, setItens] = useState<OcorrenciaResumo[]>([]);
  const [filtros, aplicarFiltros] = useFiltrosOcorrenciasUrl();

  const carregar = useCallback(async () => {
    if (legado) return;
    try {
      setItens((await ocorrenciasService.listar([], 100, 0, true, filtros)).itens);
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    }
  }, [filtros, avisar, legado]);

  useEffect(() => {
    void carregar();
  }, [carregar]);

  const abrir = useCallback((id: string) => {
    navigate(urlDoDetalhe('/minhas', id, searchParams));
  }, [navigate, searchParams]);

  if (legado) return <Navigate to={urlDoDetalhe('/minhas', legado, searchParams)} replace />;

  return (
    <div className="pagina">
      <section className="card">
        <h2>{t('ocorrencias:minhas.titulo')}</h2>
        <FiltrosOcorrenciasBar valor={filtros} onAplicar={aplicarFiltros} />
        {itens.length === 0 && <p className="muted">{t(temFiltroAtivo(filtros) ? 'ocorrencias:filtros.nenhum_resultado' : 'ocorrencias:minhas.vazio')}</p>}
        <ul className="lista clicavel">
          {itens.map((o) => (
            <li key={o.ocorrencia_id} onClick={() => abrir(o.ocorrencia_id)}>
              <span><strong>{o.numero_protocolo}</strong> · {formatarNatureza(o.natureza, t)}</span>
              <span className="lista-badges"><StatusBadge status={o.status} /><PrioridadeBadge prioridade={o.prioridade} /></span>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
};
