import React, { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Button } from '../components/common/Button';
import { BarrasHorizontais, ColunasPorHora, type ItemBarra } from '../components/indicadores/Graficos';
import { useToast } from '../hooks/useToast';
import { mensagemDeErro } from '../services/api';
import { indicadoresService } from '../services/indicadoresService';
import type { Contagem, Duracao, Indicadores } from '../types/api';
import { formatarDuracao } from '../utils/duracao';
import { formatarNatureza } from '../utils/formatarNatureza';

const PERIODOS_DIAS = [7, 30, 90] as const;
const MS_POR_DIA = 86_400_000;
const formatarPercentual = (taxa: number | null) => (taxa === null ? '—' : `${Math.round(taxa * 100)}%`);

const Tile: React.FC<{ rotulo: string; valor: string; sub?: string }> = ({ rotulo, valor, sub }) => (
  <div className="kpi-card">
    <span className="kpi-label">{rotulo}</span>
    <span className="kpi-val">{valor}</span>
    {sub && <span className="kpi-sub">{sub}</span>}
  </div>
);

const Cartao: React.FC<{ titulo: string; subtitulo?: string; children: React.ReactNode }> = ({ titulo, subtitulo, children }) => (
  <section className="card indicador-cartao">
    <h3>{titulo}</h3>
    {subtitulo && <p className="muted small">{subtitulo}</p>}
    {children}
  </section>
);

/** Sugestão #11: KPIs de RF01 (volume), RF04 (triagem) e RF02 (despacho), agregados no banco. */
export const IndicadoresPage: React.FC = () => {
  const { t } = useTranslation(['common', 'ocorrencias']);
  const { avisar } = useToast();
  const [dias, setDias] = useState<number>(30);
  const [dados, setDados] = useState<Indicadores | null>(null);
  const [carregando, setCarregando] = useState(false);

  const carregar = useCallback(async () => {
    setCarregando(true);
    try {
      const ate = new Date();
      const de = new Date(ate.getTime() - dias * MS_POR_DIA);
      setDados(await indicadoresService.obter(de.toISOString(), ate.toISOString()));
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    } finally {
      setCarregando(false);
    }
  }, [dias, avisar]);

  useEffect(() => { void carregar(); }, [carregar]);

  const amostras = (d: Duracao) => t('indicadores.amostras', { count: d.amostras });
  const barras = (itens: Contagem[], rotular: (chave: string) => string): ItemBarra[] =>
    itens.map((c) => ({ chave: c.chave, rotulo: rotular(c.chave), valor: c.total }));
  const totalDecisoes = dados?.decisoes.reduce((a, c) => a + c.total, 0) ?? 0;

  return (
    <div className="pagina indicadores">
      <div className="indicadores-cabecalho">
        <div>
          <h1>{t('indicadores.titulo')}</h1>
          <p className="muted">{t('indicadores.subtitulo')}</p>
        </div>
        <div className="indicadores-filtros" role="group" aria-label={t('indicadores.periodo')}>
          {PERIODOS_DIAS.map((d) => (
            <button key={d} className={`tab ${d === dias ? 'ativo' : ''}`} aria-pressed={d === dias} onClick={() => setDias(d)}>
              {t('indicadores.ultimos_dias', { count: d })}
            </button>
          ))}
          <Button variant="secondary" size="sm" loading={carregando} onClick={() => void carregar()}>{t('actions.atualizar')}</Button>
        </div>
      </div>

      {dados && (
        <>
          <div className="kpi-grid indicadores-kpis">
            <Tile rotulo={t('indicadores.total_ocorrencias')} valor={dados.total_ocorrencias.toLocaleString()} />
            <Tile rotulo={t('indicadores.tempo_decisao')} valor={formatarDuracao(dados.tempo_ate_decisao.media_segundos)} sub={amostras(dados.tempo_ate_decisao)} />
            <Tile rotulo={t('indicadores.tempo_validacao_despacho')} valor={formatarDuracao(dados.tempo_validacao_despacho.media_segundos)} sub={amostras(dados.tempo_validacao_despacho)} />
            <Tile rotulo={t('indicadores.tempo_despacho_encerramento')} valor={formatarDuracao(dados.tempo_despacho_encerramento.media_segundos)} sub={amostras(dados.tempo_despacho_encerramento)} />
            <Tile rotulo={t('indicadores.taxa_devolucao')} valor={formatarPercentual(dados.taxa_devolucao)} sub={t('indicadores.de_decisoes', { count: totalDecisoes })} />
            <Tile rotulo={t('indicadores.taxa_rejeicao')} valor={formatarPercentual(dados.taxa_rejeicao)} sub={t('indicadores.de_decisoes', { count: totalDecisoes })} />
          </div>

          <div className="indicadores-grade">
            <Cartao titulo={t('indicadores.por_natureza')} subtitulo={t('indicadores.criadas_no_periodo')}>
              <BarrasHorizontais
                itens={barras(dados.por_natureza, (c) => (c === 'OUTRAS' ? t('indicadores.outras') : formatarNatureza(c, t)))}
                rotuloCategoria={t('ocorrencias:form.natureza_label')}
                rotuloValor={t('indicadores.ocorrencias')}
              />
            </Cartao>
            <Cartao titulo={t('indicadores.por_faixa_horaria')} subtitulo={t('indicadores.hora_do_fato')}>
              <ColunasPorHora valores={dados.por_faixa_horaria} rotuloValor={t('indicadores.ocorrencias')} titulo={t('indicadores.por_faixa_horaria')} />
            </Cartao>
            <Cartao titulo={t('indicadores.decisoes')} subtitulo={t('indicadores.decisoes_sub')}>
              <BarrasHorizontais
                itens={dados.decisoes.map((c) => ({
                  chave: c.chave, rotulo: t(`indicadores.decisao_${c.chave}`), valor: c.total,
                  valorFormatado: `${c.total.toLocaleString()} (${formatarPercentual(totalDecisoes ? c.total / totalDecisoes : null)})`,
                }))}
                rotuloCategoria={t('indicadores.decisao')}
                rotuloValor={t('indicadores.quantidade')}
              />
            </Cartao>
            <Cartao titulo={t('indicadores.despachos_por_hora')} subtitulo={t('indicadores.despachos_sub')}>
              <ColunasPorHora valores={dados.despachos_por_hora} rotuloValor={t('indicadores.despachos')} titulo={t('indicadores.despachos_por_hora')} />
            </Cartao>
            <Cartao titulo={t('indicadores.por_origem')}>
              <BarrasHorizontais
                itens={barras(dados.por_origem, (c) => t(`ocorrencias:filtros.origem_${c}`, c))}
                rotuloCategoria={t('ocorrencias:filtros.origem')}
                rotuloValor={t('indicadores.ocorrencias')}
              />
            </Cartao>
            <Cartao titulo={t('indicadores.frota_agora')} subtitulo={t('indicadores.frota_sub')}>
              <BarrasHorizontais
                itens={barras(dados.viaturas_por_situacao, (c) => t(`situacao.${c}`, c))}
                rotuloCategoria={t('indicadores.situacao')}
                rotuloValor={t('indicadores.viaturas')}
              />
            </Cartao>
          </div>
        </>
      )}
    </div>
  );
};
