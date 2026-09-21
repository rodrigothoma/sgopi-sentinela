import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../hooks/useAuth';
import { useToast } from '../../hooks/useToast';
import { mensagemDeErro } from '../../services/api';
import { apreensoesService } from '../../services/apreensoesService';
import { STATUS_ACEITAM_APREENSAO, type AutoApreensao, type ItemApreendido, type OcorrenciaDetalhe } from '../../types/api';
import { AutoApreensaoView } from './AutoApreensaoView';
import { ItemApreendidoForm } from './ItemApreendidoForm';

const fmt = (iso: string) => new Date(iso).toLocaleString();
const MINIMO_DESTINO = 3;

interface ItemProps {
  item: ItemApreendido;
  podeMovimentar: boolean;
  onMovimentar: (item: ItemApreendido, destino: string, observacao: string) => Promise<void>;
}

const ItemApreendidoCard: React.FC<ItemProps> = ({ item, podeMovimentar, onMovimentar }) => {
  const { t } = useTranslation('ocorrencias');
  const [destino, setDestino] = useState('');
  const [observacao, setObservacao] = useState('');
  const [ocupado, setOcupado] = useState(false);
  const [mostrarCustodia, setMostrarCustodia] = useState(false);

  const movimentar = async () => {
    setOcupado(true);
    try {
      await onMovimentar(item, destino.trim(), observacao.trim());
      setDestino('');
      setObservacao('');
    } finally {
      setOcupado(false);
    }
  };

  const identificacao = [item.marca, item.calibre, item.numero_serie ? `S/N ${item.numero_serie}` : null].filter(Boolean).join(' · ');

  return (
    <li className="apreensao-item" data-cy="apreensao-item">
      <div className="apreensao-topo">
        <div>
          <strong>{item.numero_lacre}</strong> · {t(`apreensoes.tipo.${item.tipo}`)} · {item.quantidade} {t(`apreensoes.unidade.${item.unidade}`)}
          <div>{item.descricao}</div>
          <small className="muted">
            {t(`apreensoes.estado.${item.estado_conservacao}`)}{identificacao ? ` · ${identificacao}` : ''} · {t('apreensoes.registrado_em')} {fmt(item.registrado_em)}
          </small>
        </div>
        <div className="apreensao-local">
          <small className="muted">{t('apreensoes.localizacao_atual')}</small>
          <strong>{item.localizacao_atual}</strong>
        </div>
      </div>
      <button type="button" className="btn btn-link" onClick={() => setMostrarCustodia((m) => !m)}>
        {mostrarCustodia ? t('apreensoes.ocultar_custodia') : t('apreensoes.ver_custodia', { total: item.movimentacoes.length })}
      </button>
      {mostrarCustodia && (
        <ol className="historico">
          {item.movimentacoes.map((m, k) => (
            <li key={k}>
              <span className="muted">{fmt(m.em)}</span> · {m.origem ? <>{m.origem} → </> : null}<strong>{m.destino}</strong>
              {' '}· <code>{m.por_id.slice(0, 8)}</code>
              {m.observacao && <em> — {m.observacao}</em>}
            </li>
          ))}
        </ol>
      )}
      {podeMovimentar && (
        <div className="apreensao-movimentar">
          <input
            aria-label={t('apreensoes.destino_label')}
            placeholder={t('apreensoes.destino_placeholder')}
            maxLength={255}
            value={destino}
            onChange={(e) => setDestino(e.target.value)}
          />
          <input
            aria-label={t('apreensoes.observacao_label')}
            placeholder={t('apreensoes.observacao_placeholder')}
            maxLength={2000}
            value={observacao}
            onChange={(e) => setObservacao(e.target.value)}
          />
          <button type="button" className="btn btn-sm" disabled={ocupado || destino.trim().length < MINIMO_DESTINO} onClick={() => void movimentar()}>
            {t('apreensoes.movimentar')}
          </button>
        </div>
      )}
    </li>
  );
};

interface Props {
  o: OcorrenciaDetalhe;
  /** Avisa o pai que a ocorrência mudou (novo item ou custódia) para que ele recarregue o detalhe. */
  onAlterada?: () => void;
}

/** Aba de apreensões no detalhe da ocorrência (RF03 / UC03): cadastro, cadeia de custódia e Auto de Apreensão. */
export const ApreensoesAba: React.FC<Props> = ({ o, onAlterada }) => {
  const { t } = useTranslation(['ocorrencias', 'common']);
  const { usuario } = useAuth();
  const { avisar } = useToast();
  const [itens, setItens] = useState<ItemApreendido[]>(o.itens_apreendidos);
  const [ocupado, setOcupado] = useState(false);
  const [auto, setAuto] = useState<AutoApreensao | null>(null);

  useEffect(() => { setItens(o.itens_apreendidos); }, [o]);

  const ehAutor = usuario?.papel === 'AGENTE' && usuario.id === o.agente_policial_id;
  const podeRegistrar = ehAutor && STATUS_ACEITAM_APREENSAO.includes(o.status);
  const podeMovimentar = (ehAutor || usuario?.papel === 'DELEGADO') && o.status !== 'EXCLUIDA';

  const registrar = async (dto: Parameters<typeof apreensoesService.registrar>[1]) => {
    setOcupado(true);
    try {
      const item = await apreensoesService.registrar(o.ocorrencia_id, dto);
      setItens((xs) => [...xs, item]);
      avisar(t('ocorrencias:apreensoes.ok_registrado', { lacre: item.numero_lacre }), 'sucesso');
      onAlterada?.();
    } catch (err) {
      avisar(mensagemDeErro(err, t('ocorrencias:apreensoes.erro_registrar')), 'erro');
      throw err;
    } finally {
      setOcupado(false);
    }
  };

  const movimentar = async (item: ItemApreendido, destino: string, observacao: string) => {
    try {
      const atualizado = await apreensoesService.movimentar(o.ocorrencia_id, item.id, { destino, observacao: observacao || null });
      setItens((xs) => xs.map((x) => (x.id === atualizado.id ? atualizado : x)));
      avisar(t('ocorrencias:apreensoes.ok_movimentado', { lacre: item.numero_lacre, destino: atualizado.localizacao_atual }), 'sucesso');
      onAlterada?.();
    } catch (err) {
      avisar(mensagemDeErro(err, t('ocorrencias:apreensoes.erro_movimentar')), 'erro');
    }
  };

  const emitirAuto = async () => {
    setOcupado(true);
    try {
      setAuto(await apreensoesService.emitirAuto(o.ocorrencia_id));
    } catch (err) {
      avisar(mensagemDeErro(err, t('ocorrencias:apreensoes.erro_auto')), 'erro');
    } finally {
      setOcupado(false);
    }
  };

  return (
    <div className="apreensoes" data-cy="aba-apreensoes">
      <div className="detalhe-cabecalho">
        <h4 style={{ margin: 0 }}>{t('ocorrencias:apreensoes.titulo')} <span className="muted">({itens.length})</span></h4>
        <button className="btn btn-sm" disabled={ocupado || itens.length === 0} onClick={() => void emitirAuto()} data-cy="emitir-auto">
          {t('ocorrencias:apreensoes.auto.emitir')}
        </button>
      </div>
      <p className="muted small">{t('ocorrencias:apreensoes.ajuda_aba')}</p>

      {podeRegistrar && (
        <ItemApreendidoForm onAdd={registrar} lacresEmUso={itens.map((i) => i.numero_lacre)} ocupado={ocupado} rotuloAdicionar={t('ocorrencias:apreensoes.registrar')} />
      )}
      {!podeRegistrar && ehAutor && <p className="muted small">{t('ocorrencias:apreensoes.status_bloqueado')}</p>}

      {itens.length === 0 ? (
        <p className="muted">{t('ocorrencias:apreensoes.vazio')}</p>
      ) : (
        <ul className="lista apreensoes-lista">
          {itens.map((item) => (
            <ItemApreendidoCard key={item.id} item={item} podeMovimentar={podeMovimentar} onMovimentar={movimentar} />
          ))}
        </ul>
      )}

      {auto && <AutoApreensaoView auto={auto} onFechar={() => setAuto(null)} />}
    </div>
  );
};
