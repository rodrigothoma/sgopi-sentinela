import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';

/**
 * Gráficos de série única do painel de indicadores (sugestão #11).
 * Uma cor só (a primária do tema, validada contra as superfícies clara e escura), marcas finas com
 * ponta arredondada, valor na ponta em cor de texto, tooltip ao passar o mouse e tabela equivalente.
 */

export interface ItemBarra {
  chave: string;
  rotulo: string;
  valor: number;
  /** Texto exibido no lugar do número (ex.: percentual) — o comprimento continua sendo ``valor``. */
  valorFormatado?: string;
}

const formatarNumero = (n: number) => n.toLocaleString();

const TabelaAlternativa: React.FC<{ cabecalho: [string, string]; linhas: [string, string][] }> = ({ cabecalho, linhas }) => {
  const { t } = useTranslation('common');
  return (
    <details className="grafico-tabela">
      <summary className="muted small">{t('indicadores.ver_tabela')}</summary>
      <table>
        <thead><tr><th scope="col">{cabecalho[0]}</th><th scope="col">{cabecalho[1]}</th></tr></thead>
        <tbody>{linhas.map(([a, b]) => <tr key={a}><td>{a}</td><td>{b}</td></tr>)}</tbody>
      </table>
    </details>
  );
};

/** Barras horizontais: magnitude por categoria, ordenadas pelo chamador. */
export const BarrasHorizontais: React.FC<{ itens: ItemBarra[]; rotuloValor: string; rotuloCategoria: string }> = ({
  itens, rotuloValor, rotuloCategoria,
}) => {
  const { t } = useTranslation('common');
  const maximo = Math.max(1, ...itens.map((i) => i.valor));
  if (itens.length === 0) return <p className="muted">{t('indicadores.sem_dados')}</p>;
  return (
    <>
      <ul className="barras-h" role="list">
        {itens.map((i) => {
          const texto = i.valorFormatado ?? formatarNumero(i.valor);
          return (
            <li key={i.chave} className="barras-h-linha" title={`${i.rotulo}: ${texto}`}>
              <span className="barras-h-rotulo">{i.rotulo}</span>
              <span className="barras-h-trilho">
                <span className="barras-h-barra" style={{ width: `${(i.valor / maximo) * 100}%` }} />
                <span className="barras-h-valor">{texto}</span>
              </span>
            </li>
          );
        })}
      </ul>
      <TabelaAlternativa cabecalho={[rotuloCategoria, rotuloValor]} linhas={itens.map((i) => [i.rotulo, i.valorFormatado ?? formatarNumero(i.valor)])} />
    </>
  );
};

const LARGURA = 480;
const ALTURA = 160;
const MARGEM = { topo: 16, direita: 8, base: 22, esquerda: 28 };
const LARGURA_MAXIMA_COLUNA = 24;
const RAIO_PONTA = 4;
const VAO = 2;

/** Arredonda o topo do eixo para um número "limpo" (1, 2, 5 × 10ⁿ). */
function tetoLimpo(valor: number): number {
  if (valor <= 0) return 1;
  const potencia = 10 ** Math.floor(Math.log10(valor));
  const passo = [1, 2, 5, 10].find((m) => m * potencia >= valor) ?? 10;
  return passo * potencia;
}

/** Caminho de coluna com ponta arredondada (4px) e base reta. */
function caminhoColuna(x: number, y: number, largura: number, altura: number): string {
  const r = Math.min(RAIO_PONTA, largura / 2, altura);
  const base = y + altura;
  return `M${x},${base} V${y + r} Q${x},${y} ${x + r},${y} H${x + largura - r} Q${x + largura},${y} ${x + largura},${y + r} V${base} Z`;
}

/** 24 colunas (uma por hora do dia, no fuso do navegador) com tooltip por coluna. */
export const ColunasPorHora: React.FC<{ valores: number[]; rotuloValor: string; titulo: string }> = ({ valores, rotuloValor, titulo }) => {
  const { t } = useTranslation('common');
  const [foco, setFoco] = useState<number | null>(null);
  const teto = tetoLimpo(Math.max(...valores, 0));
  const largura = LARGURA - MARGEM.esquerda - MARGEM.direita;
  const altura = ALTURA - MARGEM.topo - MARGEM.base;
  const faixa = largura / valores.length;
  const coluna = Math.min(LARGURA_MAXIMA_COLUNA, faixa - VAO);
  const y = (v: number) => MARGEM.topo + altura - (v / teto) * altura;
  const faixaHora = (h: number) => t('indicadores.faixa_hora', { de: String(h).padStart(2, '0'), ate: String((h + 1) % 24).padStart(2, '0') });
  const maximo = valores.indexOf(Math.max(...valores));
  const total = valores.reduce((a, b) => a + b, 0);

  return (
    <>
      <div className="colunas-hora">
        <svg viewBox={`0 0 ${LARGURA} ${ALTURA}`} role="img" aria-label={titulo} onMouseLeave={() => setFoco(null)}>
          {[0, teto / 2, teto].map((v) => (
            <g key={v}>
              <line x1={MARGEM.esquerda} x2={LARGURA - MARGEM.direita} y1={y(v)} y2={y(v)} className="grafico-grade" />
              <text x={MARGEM.esquerda - 6} y={y(v)} className="grafico-eixo" textAnchor="end" dominantBaseline="middle">{formatarNumero(v)}</text>
            </g>
          ))}
          {valores.map((v, h) => {
            const x = MARGEM.esquerda + h * faixa + (faixa - coluna) / 2;
            return (
              <g key={h} onMouseEnter={() => setFoco(h)}>
                {/* alvo de hover do tamanho da faixa inteira, maior que a coluna */}
                <rect x={MARGEM.esquerda + h * faixa} y={MARGEM.topo} width={faixa} height={altura} fill="transparent" />
                {v > 0 && <path d={caminhoColuna(x, y(v), coluna, y(0) - y(v))} className={`grafico-marca ${foco === h ? 'foco' : ''}`} />}
                {h % 3 === 0 && (
                  <text x={MARGEM.esquerda + h * faixa + faixa / 2} y={ALTURA - 6} className="grafico-eixo" textAnchor="middle">{String(h).padStart(2, '0')}h</text>
                )}
              </g>
            );
          })}
          {total > 0 && foco === null && (
            <text x={MARGEM.esquerda + maximo * faixa + faixa / 2} y={y(valores[maximo]) - 4} className="grafico-valor" textAnchor="middle">
              {formatarNumero(valores[maximo])}
            </text>
          )}
        </svg>
        {foco !== null && (
          <div className="grafico-tooltip" style={{ left: `${Math.min(85, Math.max(15, ((MARGEM.esquerda + foco * faixa + faixa / 2) / LARGURA) * 100))}%` }} role="status">
            <strong>{faixaHora(foco)}</strong> · {rotuloValor}: {formatarNumero(valores[foco])}
          </div>
        )}
      </div>
      <TabelaAlternativa
        cabecalho={[t('indicadores.hora'), rotuloValor]}
        linhas={valores.map((v, h) => [faixaHora(h), formatarNumero(v)])}
      />
    </>
  );
};
