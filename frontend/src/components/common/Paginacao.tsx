import React from 'react';
import { useTranslation } from 'react-i18next';
import { faixaDaPagina, totalDePaginas } from '../../utils/paginacao';
import './Paginacao.css';

interface Props {
  pagina: number;
  porPagina: number;
  total: number;
  onMudarPagina: (pagina: number) => void;
  carregando?: boolean;
}

/** Navegação de lista paginada no servidor: "Exibindo 1–50 de 237 · Página 1 de 5". */
export const Paginacao: React.FC<Props> = ({ pagina, porPagina, total, onMudarPagina, carregando = false }) => {
  const { t } = useTranslation('common');
  const paginas = totalDePaginas(total, porPagina);
  const { inicio, fim } = faixaDaPagina(pagina, porPagina, total);

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
      </div>
    </nav>
  );
};
