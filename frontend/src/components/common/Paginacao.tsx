import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { RETICENCIAS, faixaDaPagina, paginaValida, paginasVisiveis, totalDePaginas } from '../../utils/paginacao';
import './Paginacao.css';

interface Props {
  pagina: number;
  porPagina: number;
  total: number;
  onMudarPagina: (pagina: number) => void;
  carregando?: boolean;
}

/** Navegação de lista paginada no servidor: anterior/próxima, números das páginas e "Ir para". */
export const Paginacao: React.FC<Props> = ({ pagina, porPagina, total, onMudarPagina, carregando = false }) => {
  const { t } = useTranslation('common');
  const [destino, setDestino] = useState('');
  const paginas = totalDePaginas(total, porPagina);
  const { inicio, fim } = faixaDaPagina(pagina, porPagina, total);

  const irPara = (e: React.FormEvent) => {
    e.preventDefault();
    const alvo = paginaValida(destino, paginas);
    if (alvo !== null && alvo !== pagina) onMudarPagina(alvo);
    setDestino('');
  };

  return (
    <nav className="paginacao" aria-label={t('paginacao.navegacao')} data-cy="paginacao">
      <span className="paginacao-info">
        {t('paginacao.exibindo', { inicio, fim, total })} · {t('paginacao.pagina_de', { pagina, total: paginas })}
      </span>
      <div className="paginacao-botoes">
        <button
          type="button"
          className="btn btn-sm btn-outline"
          onClick={() => onMudarPagina(pagina - 1)}
          disabled={carregando || pagina <= 1}
          title={t('paginacao.anterior')}
          aria-label={t('paginacao.anterior')}
          data-cy="paginacao-anterior"
        >
          &lt;
        </button>
        {paginasVisiveis(pagina, paginas).map((item, i) =>
          item === RETICENCIAS ? (
            <span key={`reticencias-${i}`} className="paginacao-reticencias" aria-hidden="true">
              {RETICENCIAS}
            </span>
          ) : (
            <button
              key={item}
              type="button"
              className={`btn btn-sm ${item === pagina ? 'btn-primary paginacao-atual' : 'btn-outline'}`}
              onClick={() => onMudarPagina(item)}
              disabled={carregando || item === pagina}
              aria-current={item === pagina ? 'page' : undefined}
              aria-label={t('paginacao.pagina_n', { pagina: item })}
              data-cy={`paginacao-pagina-${item}`}
            >
              {item}
            </button>
          ),
        )}
        <button
          type="button"
          className="btn btn-sm btn-outline"
          onClick={() => onMudarPagina(pagina + 1)}
          disabled={carregando || pagina >= paginas}
          title={t('paginacao.proxima')}
          aria-label={t('paginacao.proxima')}
          data-cy="paginacao-proxima"
        >
          &gt;
        </button>
        {paginas > 1 && (
          <form className="paginacao-ir" onSubmit={irPara}>
            <label htmlFor="paginacao-destino">{t('paginacao.ir_para')}</label>
            <input
              id="paginacao-destino"
              type="number"
              min={1}
              max={paginas}
              value={destino}
              onChange={(e) => setDestino(e.target.value)}
              disabled={carregando}
              data-cy="paginacao-ir-para"
            />
          </form>
        )}
      </div>
    </nav>
  );
};
