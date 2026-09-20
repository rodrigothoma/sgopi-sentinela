import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import { mensagemDeErro } from '../../services/api';
import { ocorrenciasService } from '../../services/ocorrenciasService';
import type { Evidencia, OcorrenciaDetalhe as Detalhe } from '../../types/api';
import { StatusBadge } from '../StatusBadge';
import { formatarNatureza } from '../../utils/formatarNatureza';

const fmt = (iso: string) => new Date(iso).toLocaleString();

type EstadoVisual = 'CARREGANDO' | 'INTEGRA' | 'DIVERGENTE' | 'INDISPONIVEL' | 'ERRO';

const EvidenciaItem: React.FC<{ ocorrenciaId: string; evidencia: Evidencia }> = ({ ocorrenciaId, evidencia }) => {
  const { t } = useTranslation(['ocorrencias']);
  const [estado, setEstado] = useState<EstadoVisual>('CARREGANDO');
  const [erro, setErro] = useState<string | null>(null);
  const [baixando, setBaixando] = useState(false);

  useEffect(() => {
    let ativo = true;
    setEstado('CARREGANDO');
    setErro(null);
    ocorrenciasService.verificarIntegridade(ocorrenciaId, evidencia.id)
      .then((resultado) => { if (ativo) setEstado(resultado.estado); })
      .catch((falha) => {
        if (!ativo) return;
        const indisponivel = falha?.response?.status === 404;
        setEstado(indisponivel ? 'INDISPONIVEL' : 'ERRO');
        setErro(mensagemDeErro(falha, t('ocorrencias:evidencias.integridade_erro')));
      });
    return () => { ativo = false; };
  }, [ocorrenciaId, evidencia.id, t]);

  const baixar = async () => {
    setBaixando(true);
    setErro(null);
    try {
      await ocorrenciasService.baixarEvidencia(ocorrenciaId, evidencia);
    } catch (falha) {
      if (axios.isAxiosError(falha) && falha.response?.status === 409) setEstado('DIVERGENTE');
      if (axios.isAxiosError(falha) && falha.response?.status === 404) setEstado('INDISPONIVEL');
      setErro(mensagemDeErro(falha, t('ocorrencias:evidencias.download_erro')));
    } finally {
      setBaixando(false);
    }
  };

  const classe = estado === 'INTEGRA' ? 'ok' : estado === 'CARREGANDO' ? 'muted' : 'erro';
  return (
    <li className="evidencia-item">
      <div>
        <strong>{evidencia.nome_original}</strong> · {evidencia.formato.toUpperCase()} · {(evidencia.tamanho / 1024).toFixed(1)} KB · {fmt(evidencia.enviada_em)}
      </div>
      <div className="evidencia-hash"><strong>SHA-256:</strong> <code>{evidencia.hash_sha256}</code></div>
      <div className="evidencia-acoes">
        <span className={classe}>{t(`ocorrencias:evidencias.integridade_${estado.toLowerCase()}`)}</span>
        <button className="btn btn-sm" disabled={estado !== 'INTEGRA' || baixando} onClick={baixar}>
          {baixando ? t('ocorrencias:evidencias.baixando') : t('ocorrencias:evidencias.download')}
        </button>
      </div>
      {erro && <small className="erro">{erro}</small>}
    </li>
  );
};

export const OcorrenciaDetalheView: React.FC<{ o: Detalhe }> = ({ o }) => {
  const { t } = useTranslation(['ocorrencias', 'common']);
  const isOnline = o.envolvidos.some((e) => e.tipo === 'COMUNICANTE');

  return (
    <div className="detalhe">
      <div className="detalhe-cabecalho">
        <h2>
          {o.numero_protocolo} <StatusBadge status={o.status} />
        </h2>
        <span className="muted">
          <span style={{ fontWeight: 600, color: isOnline ? 'var(--primary)' : 'inherit' }}>
            {isOnline ? t('ocorrencias:detalhe.canal_online') : t('ocorrencias:detalhe.canal_presencial')}
          </span>{' '}
          · {t('ocorrencias:detalhe.versao')} {o.versao} · {t('ocorrencias:detalhe.registrada_em')} {fmt(o.criada_em)}
        </span>
      </div>
      <dl className="grid2">
        <dt>{t('ocorrencias:form.natureza_label')}</dt><dd>{formatarNatureza(o.natureza, t)}</dd>
        <dt>{t('ocorrencias:form.data_hora_fato_label')}</dt><dd>{fmt(o.data_hora_fato)}</dd>
        <dt>{t('ocorrencias:form.localizacao_label')}</dt><dd>{o.localizacao}</dd>
        <dt>{t('ocorrencias:form.coordenada_label')}</dt><dd>{o.latitude.toFixed(5)}, {o.longitude.toFixed(5)}</dd>
      </dl>
      <h4>{t('ocorrencias:form.descricao_label')}</h4>
      <p className="narrativa">{o.descricao}</p>
      {o.narrativa_integra !== null && (
        <p className={o.narrativa_integra ? 'ok' : 'erro'}>
          {o.narrativa_integra ? t('ocorrencias:detalhe.integra') : t('ocorrencias:detalhe.adulterada')} · SHA-256 {o.hash_narrativa?.slice(0, 12)}…
        </p>
      )}
      {o.justificativa_revisao && (
        <div className="callout">
          <strong>{t('ocorrencias:detalhe.justificativa')}:</strong> {o.justificativa_revisao}
        </div>
      )}
      {o.desfecho && (
        <div className="callout">
          <strong>{t('ocorrencias:detalhe.desfecho')}:</strong> {o.desfecho}
        </div>
      )}
      <h4>{t('ocorrencias:form.envolvidos_label')}</h4>
      <ul className="lista">
        {o.envolvidos.map((e) => (
          <li key={e.id}>
            <strong>{e.nome}</strong> · {t(`ocorrencias:envolvido.${e.tipo}`, e.tipo)}
            {e.documento ? ` · ${e.documento}` : ''}
            {e.email ? ` · ${e.email}` : ''}
            {e.telefone ? ` · ${e.telefone}` : ''}
          </li>
        ))}
      </ul>
      {o.tipificacoes.length > 0 && (
        <>
          <h4>{t('ocorrencias:form.tipificacoes_label')}</h4>
          <ul className="lista">
            {o.tipificacoes.map((tp, i) => (
              <li key={i}><strong>{tp.artigo}</strong> — {tp.descricao}</li>
            ))}
          </ul>
        </>
      )}
      {o.evidencias.length > 0 && (
        <>
          <h4>{t('ocorrencias:evidencias.titulo')}</h4>
          <ul className="lista">
            {o.evidencias.map((e) => (
              <EvidenciaItem key={e.id} ocorrenciaId={o.ocorrencia_id} evidencia={e} />
            ))}
          </ul>
        </>
      )}
      <h4>{t('ocorrencias:detalhe.historico')}</h4>
      <ol className="historico">
        {o.historico_status.map((h, i) => (
          <li key={i}>
            <span className="muted">{fmt(h.em)}</span> {h.de ? <><StatusBadge status={h.de} /> → </> : null}
            <StatusBadge status={h.para} />
            {h.justificativa && <em> — {h.justificativa}</em>}
          </li>
        ))}
      </ol>
    </div>
  );
};
