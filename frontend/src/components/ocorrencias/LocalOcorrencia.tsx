import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { SeletorCoordenada } from '../painel/SeletorCoordenada';
import { geocodificacaoService } from '../../services/geocodificacaoService';

export interface ValoresLocal { localizacao: string; latitude: number | null; longitude: number | null }

interface Props {
  valor: ValoresLocal;
  onChange: (patch: Partial<ValoresLocal>) => void;
}

type Modo = 'endereco' | 'mapa';
type EstadoBusca = 'ocioso' | 'buscando' | 'ok' | 'falha';

const fmt = (n: number) => n.toFixed(5);

/**
 * Local do fato (DEC-03): por padrão mostra o campo de endereço com a dica de que o
 * ponto pode ser escolhido no mapa. No modo mapa, um único clique define o endereço
 * (geocodificação reversa) e as coordenadas de latitude/longitude ao mesmo tempo.
 */
export const LocalOcorrencia: React.FC<Props> = ({ valor, onChange }) => {
  const { t } = useTranslation('ocorrencias');
  const [modo, setModo] = useState<Modo>('endereco');
  const [busca, setBusca] = useState<EstadoBusca>('ocioso');
  const [reverso, setReverso] = useState<EstadoBusca>('ocioso');
  const requisicao = useRef(0); // descarta respostas de cliques anteriores
  const abortRef = useRef<AbortController | null>(null);
  const onChangeRef = useRef(onChange);
  onChangeRef.current = onChange;

  useEffect(() => () => abortRef.current?.abort(), []);

  /** Clique/arraste no mapa: coordenada imediata + endereço provisório, depois o endereço real. */
  const aoMarcar = useCallback(
    (lat: number, lon: number) => {
      const provisorio = t('form.marcado_no_mapa', { lat: fmt(lat), lon: fmt(lon) });
      onChangeRef.current({ latitude: lat, longitude: lon, localizacao: provisorio });
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;
      const id = ++requisicao.current;
      setReverso('buscando');
      geocodificacaoService.reverso(lat, lon, controller.signal).then((endereco) => {
        if (id !== requisicao.current) return;
        if (endereco) {
          onChangeRef.current({ localizacao: endereco });
          setReverso('ok');
        } else {
          setReverso('falha');
        }
      });
    },
    [t],
  );

  const localizarEndereco = async () => {
    const texto = valor.localizacao.trim();
    if (!texto) return;
    setBusca('buscando');
    const achado = await geocodificacaoService.buscar(texto);
    if (!achado) {
      setBusca('falha');
      return;
    }
    onChange({ latitude: achado.latitude, longitude: achado.longitude });
    setBusca('ok');
  };

  const temCoordenada = valor.latitude !== null && valor.longitude !== null;
  const editarEndereco = (e: React.ChangeEvent<HTMLInputElement>) => {
    setBusca('ocioso');
    onChange({ localizacao: e.target.value });
  };

  const resumoCoordenada = (
    <p className={`coordenada-resumo ${temCoordenada ? 'ok' : 'pendente'}`}>
      {temCoordenada
        ? t('form.coordenada_definida', { lat: fmt(valor.latitude as number), lon: fmt(valor.longitude as number) })
        : t('form.coordenada_pendente')}
    </p>
  );

  if (modo === 'mapa') {
    return (
      <div className="local-fato">
        <p className="dica">{t('form.mapa_instrucao')}</p>
        <SeletorCoordenada latitude={valor.latitude} longitude={valor.longitude} onChange={aoMarcar} />
        <label htmlFor="localizacao">
          {t('form.localizacao_label')} <span className="obrigatorio">*</span>{' '}
          <span className="muted contador">
            {reverso === 'buscando' ? t('form.buscando_endereco') : temCoordenada ? t('form.endereco_do_mapa') : ''}
          </span>
        </label>
        <input id="localizacao" value={valor.localizacao} onChange={editarEndereco} placeholder={t('form.localizacao_placeholder')} maxLength={500} />
        {resumoCoordenada}
        <div className="modo-local">
          <button type="button" className="btn btn-ghost btn-sm" onClick={() => setModo('endereco')}>{t('form.informar_endereco')}</button>
        </div>
      </div>
    );
  }

  return (
    <div className="local-fato">
      <label htmlFor="localizacao">
        {t('form.localizacao_label')} <span className="obrigatorio">*</span>
      </label>
      <div className="modo-local">
        <input id="localizacao" value={valor.localizacao} onChange={editarEndereco} placeholder={t('form.localizacao_placeholder')} maxLength={500} style={{ flex: 1 }} />
        <button type="button" className="btn btn-sm" disabled={busca === 'buscando' || !valor.localizacao.trim()} onClick={localizarEndereco}>
          {busca === 'buscando' ? t('form.localizando') : t('form.localizar_endereco')}
        </button>
      </div>
      <p className="dica">
        {t('form.localizacao_dica')}
        <button type="button" className="btn-link" onClick={() => setModo('mapa')}>{t('form.escolher_no_mapa')} →</button>
      </p>
      {busca === 'falha' && <p className="campo-erro">{t('form.endereco_nao_localizado')}</p>}
      {busca === 'ok' && <p className="coordenada-resumo ok">{t('form.endereco_localizado')}</p>}
      {resumoCoordenada}
      <details>
        <summary>{t('form.coordenada_manual')}</summary>
        <div className="grid2">
          <label>
            Latitude
            <input type="number" step="0.000001" min={-90} max={90} value={valor.latitude ?? ''} onChange={(e) => onChange({ latitude: e.target.value === '' ? null : Number(e.target.value) })} />
          </label>
          <label>
            Longitude
            <input type="number" step="0.000001" min={-180} max={180} value={valor.longitude ?? ''} onChange={(e) => onChange({ longitude: e.target.value === '' ? null : Number(e.target.value) })} />
          </label>
        </div>
      </details>
    </div>
  );
};
