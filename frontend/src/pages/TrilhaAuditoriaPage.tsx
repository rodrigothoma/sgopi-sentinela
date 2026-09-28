import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { GlideSelect, GlideSelectOption } from '../components/common/GlideSelect';
import { Button } from '../components/common/Button';
import { StatusBadge } from '../components/StatusBadge';
import { useToast } from '../hooks/useToast';
import { mensagemDeErro } from '../services/api';
import { auditoriaService } from '../services/auditoriaService';
import type { RegistroAuditoria } from '../types/api';

const OPERACOES: string[] = [
  'ocorrencia.registrar',
  'ocorrencia.validar',
  'ocorrencia.rejeitar',
  'ocorrencia.devolver_para_correcao',
  'ocorrencia.corrigir',
  'ocorrencia.reenviar',
  'ocorrencia.encerrar',
  'despacho.criar',
  'viatura.cadastrar',
  'viatura.alterar_situacao',
  'auth.login',
  'auth.login_negado',
  'auth.acesso_negado',
  'evidencia.anexar',
  'evidencia.download',
  'evidencia.verificar_integridade',
];

const ENTIDADES: string[] = [
  'Ocorrencia',
  'Viatura',
  'OrdemDeDespacho',
  'Evidencia',
  'Usuario',
];

function getBadgeClasse(operacao: string): string {
  if (operacao.includes('rejeitar') || operacao.includes('negado')) {
    return 'badge-auditoria-danger';
  }
  if (operacao.includes('validar') || operacao.includes('registrar')) {
    return 'badge-auditoria-ok';
  }
  if (operacao.includes('devolver') || operacao.includes('corrigir') || operacao.includes('alterar')) {
    return 'badge-auditoria-warn';
  }
  return 'badge-auditoria-info';
}

/**
 * Painel de Trilha de Auditoria Imutável (RNF02 / RNF03).
 * Acesso exclusivo: DELEGADO e SUPERVISOR.
 */
export const TrilhaAuditoriaPage: React.FC = () => {
  const { t } = useTranslation('common');
  const { avisar } = useToast();

  const [registros, setRegistros] = useState<RegistroAuditoria[]>([]);
  const [carregando, setCarregando] = useState<boolean>(false);
  const [busca, setBusca] = useState<string>('');
  const [filtroOperacao, setFiltroOperacao] = useState<string>('TODAS');
  const [filtroEntidade, setFiltroEntidade] = useState<string>('TODAS');
  const [detalheSelecionado, setDetalheSelecionado] = useState<RegistroAuditoria | null>(null);
  const [abaModal, setAbaModal] = useState<'amigavel' | 'json'>('amigavel');
  const [copiado, setCopiado] = useState<boolean>(false);

  const carregar = useCallback(async () => {
    setCarregando(true);
    try {
      const params: { operacao?: string; entidade?: string; limit: number } = { limit: 200 };
      if (filtroOperacao !== 'TODAS') params.operacao = filtroOperacao;
      if (filtroEntidade !== 'TODAS') params.entidade = filtroEntidade;
      const data = await auditoriaService.listar(params);
      setRegistros(data);
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    } finally {
      setCarregando(false);
    }
  }, [filtroOperacao, filtroEntidade, avisar]);

  useEffect(() => {
    carregar();
  }, [carregar]);

  const opcoesOperacao: GlideSelectOption[] = useMemo(() => {
    return [
      { value: 'TODAS', label: t('auditoria.filtro_todas_operacoes') },
      ...OPERACOES.map((op) => ({
        value: op,
        label: t(`auditoria.operacoes.${op}`, op),
      })),
    ];
  }, [t]);

  const opcoesEntidade: GlideSelectOption[] = useMemo(() => {
    return [
      { value: 'TODAS', label: t('auditoria.filtro_todas_entidades') },
      ...ENTIDADES.map((ent) => ({ value: ent, label: ent })),
    ];
  }, [t]);

  const registrosFiltrados = useMemo(() => {
    const termo = busca.trim().toLowerCase();
    if (!termo) return registros;
    return registros.filter((r) => {
      const matchId = r.entidade_id ? r.entidade_id.toLowerCase().includes(termo) : false;
      const matchIdAmigavel = r.identificador_amigavel ? r.identificador_amigavel.toLowerCase().includes(termo) : false;
      const matchOpTecnica = r.operacao.toLowerCase().includes(termo);
      const matchOpAmigavel = t(`auditoria.operacoes.${r.operacao}`, r.operacao).toLowerCase().includes(termo);
      const matchEnt = r.entidade.toLowerCase().includes(termo);
      const matchQuem = r.quem ? r.quem.toLowerCase().includes(termo) : false;
      const matchAutorNome = r.autor_nome ? r.autor_nome.toLowerCase().includes(termo) : false;
      const matchIp = r.ip ? r.ip.toLowerCase().includes(termo) : false;
      return matchId || matchIdAmigavel || matchOpTecnica || matchOpAmigavel || matchEnt || matchQuem || matchAutorNome || matchIp;
    });
  }, [registros, busca, t]);

  const kpis = useMemo(() => {
    const total = registros.length;
    const mutacoes = registros.filter((r) => !r.operacao.startsWith('auth.')).length;
    const acessos = registros.filter((r) => r.operacao.startsWith('auth.')).length;
    return { total, mutacoes, acessos };
  }, [registros]);

  const temAntes = Boolean(detalheSelecionado?.dados_antes && Object.keys(detalheSelecionado.dados_antes).length > 0);
  const temDepois = Boolean(detalheSelecionado?.dados_depois && Object.keys(detalheSelecionado.dados_depois).length > 0);

  const chavesComparacao = useMemo(() => {
    if (!detalheSelecionado) return [];
    const antesKeys = detalheSelecionado.dados_antes ? Object.keys(detalheSelecionado.dados_antes) : [];
    const depoisKeys = detalheSelecionado.dados_depois ? Object.keys(detalheSelecionado.dados_depois) : [];
    return Array.from(new Set([...antesKeys, ...depoisKeys]));
  }, [detalheSelecionado]);

  const handleCopiarJson = useCallback(() => {
    if (!detalheSelecionado) return;
    const payload = {
      operacao: detalheSelecionado.operacao,
      entidade: detalheSelecionado.entidade,
      entidade_id: detalheSelecionado.entidade_id,
      dados_antes: detalheSelecionado.dados_antes,
      dados_depois: detalheSelecionado.dados_depois,
      quando: detalheSelecionado.quando,
      quem: detalheSelecionado.quem,
      ip: detalheSelecionado.ip,
    };
    if (navigator?.clipboard?.writeText) {
      navigator.clipboard
        .writeText(JSON.stringify(payload, null, 2))
        .then(() => {
          setCopiado(true);
          setTimeout(() => setCopiado(false), 2000);
        })
        .catch(() => {
          avisar(t('errors.unexpected', 'Erro ao copiar para a área de transferência'), 'erro');
        });
    }
  }, [detalheSelecionado, avisar, t]);

  const formatarValor = useCallback((chave: string, valor: unknown) => {
    if (valor === null || valor === undefined) {
      return <span className="muted" style={{ fontStyle: 'italic' }}>—</span>;
    }
    if (typeof valor === 'boolean') {
      return (
        <span style={{ fontWeight: 600, color: valor ? 'var(--ok)' : 'var(--danger)' }}>
          {valor ? t('auditoria.sim') : t('auditoria.nao')}
        </span>
      );
    }
    const strVal = String(valor);
    if (chave === 'status' || chave.endsWith('_status')) {
      return <StatusBadge status={strVal} grupo="status" />;
    }
    if (chave === 'situacao' || chave.endsWith('_situacao')) {
      return <StatusBadge status={strVal} grupo="situacao" />;
    }
    if (typeof valor === 'object') {
      return (
        <pre
          style={{
            margin: 0,
            padding: '6px 8px',
            background: 'var(--bg)',
            borderRadius: 6,
            fontSize: '0.78rem',
            maxHeight: 120,
            overflow: 'auto',
            border: '1px solid var(--line)',
          }}
        >
          {JSON.stringify(valor, null, 2)}
        </pre>
      );
    }
    if (typeof valor === 'string' && valor.length >= 40 && /^[a-fA-F0-9]+$/.test(valor)) {
      return (
        <span
          style={{
            fontFamily: 'monospace',
            fontSize: '0.8rem',
            background: 'var(--bg)',
            padding: '2px 6px',
            borderRadius: 4,
            border: '1px solid var(--line)',
          }}
          title={valor}
        >
          {valor.slice(0, 10)}...{valor.slice(-8)}
        </span>
      );
    }
    return <span style={{ fontWeight: 500 }}>{strVal}</span>;
  }, [t]);

  return (
    <div className="pagina" style={{ maxWidth: 1240, margin: '0 auto', padding: '24px 16px' }}>
      {/* Cabeçalho da Trilha de Auditoria */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16, marginBottom: 20 }}>
        <div>
          <h1 style={{ margin: '0 0 4px' }}>{t('auditoria.titulo')}</h1>
          <p className="muted" style={{ margin: 0, maxWidth: 780 }}>
            {t('auditoria.subtitulo')}
          </p>
        </div>
        <Button variant="secondary" size="sm" loading={carregando} onClick={carregar}>
          {t('actions.atualizar')}
        </Button>
      </div>

      {/* KPI Cards */}
      <div className="kpi-grid" style={{ marginBottom: 20 }}>
        <div className="kpi-card">
          <span className="kpi-label">{t('auditoria.kpi_total')}</span>
          <span className="kpi-val">{kpis.total}</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-label">{t('auditoria.kpi_mutacoes')}</span>
          <span className="kpi-val" style={{ color: 'var(--primary)' }}>{kpis.mutacoes}</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-label">{t('auditoria.kpi_acessos')}</span>
          <span className="kpi-val" style={{ color: 'var(--ok)' }}>{kpis.acessos}</span>
        </div>
      </div>

      {/* Barra de Filtros e Busca */}
      <div
        className="card"
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: 12,
          alignItems: 'center',
          padding: '14px 16px',
          marginBottom: 16,
        }}
      >
        <div style={{ flex: '1 1 280px' }}>
          <input
            type="text"
            placeholder={t('auditoria.pesquisar_placeholder')}
            value={busca}
            onChange={(e) => setBusca(e.target.value)}
            style={{
              width: '100%',
              padding: '8px 12px',
              borderRadius: 8,
              border: '1px solid var(--line)',
              background: 'var(--bg)',
              color: 'var(--ink)',
              fontSize: '0.88rem',
            }}
          />
        </div>

        <div style={{ minWidth: 200 }}>
          <GlideSelect
            options={opcoesOperacao}
            value={filtroOperacao}
            onChange={(val) => setFiltroOperacao(val)}
            size="sm"
            menuWidth={260}
            ariaLabel={t('auditoria.filtro_operacao')}
          />
        </div>

        <div style={{ minWidth: 160 }}>
          <GlideSelect
            options={opcoesEntidade}
            value={filtroEntidade}
            onChange={(val) => setFiltroEntidade(val)}
            size="sm"
            menuWidth={180}
            ariaLabel={t('auditoria.filtro_entidade')}
          />
        </div>
      </div>

      {/* Tabela de Registros de Auditoria */}
      <div className="card" style={{ padding: 0, overflowX: 'auto' }}>
        <table className="tabela" style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              <th style={{ textAlign: 'left', padding: '12px 16px' }}>{t('auditoria.coluna_quando')}</th>
              <th style={{ textAlign: 'left', padding: '12px 16px' }}>{t('auditoria.coluna_operacao')}</th>
              <th style={{ textAlign: 'left', padding: '12px 16px' }}>{t('auditoria.coluna_entidade')}</th>
              <th style={{ textAlign: 'left', padding: '12px 16px' }}>{t('auditoria.coluna_id')}</th>
              <th style={{ textAlign: 'left', padding: '12px 16px' }}>{t('auditoria.coluna_autor')}</th>
              <th style={{ textAlign: 'left', padding: '12px 16px' }}>{t('auditoria.coluna_ip')}</th>
              <th style={{ textAlign: 'center', padding: '12px 16px' }}>{t('auditoria.coluna_acoes')}</th>
            </tr>
          </thead>
          <tbody>
            {registrosFiltrados.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ textAlign: 'center', padding: '36px 16px', color: 'var(--muted)' }}>
                  {t('auditoria.vazio')}
                </td>
              </tr>
            ) : (
              registrosFiltrados.map((reg) => (
                <tr key={reg.id} style={{ borderBottom: '1px solid var(--line)' }}>
                  <td style={{ padding: '12px 16px', whiteSpace: 'nowrap', fontSize: '0.85rem' }}>
                    <strong>{new Date(reg.quando).toLocaleDateString()}</strong>
                    <br />
                    <span className="muted">{new Date(reg.quando).toLocaleTimeString()}</span>
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    <span
                      className={`badge-auditoria ${getBadgeClasse(reg.operacao)}`}
                      title={reg.operacao}
                    >
                      {t(`auditoria.operacoes.${reg.operacao}`, reg.operacao)}
                    </span>
                  </td>
                  <td style={{ padding: '12px 16px', fontWeight: 500 }}>
                    {reg.entidade}
                  </td>
                  <td style={{ padding: '12px 16px', fontSize: '0.85rem' }}>
                    {reg.identificador_amigavel ? (
                      <div>
                        <strong style={{ fontFamily: 'monospace', color: 'var(--ink)' }}>
                          {reg.identificador_amigavel}
                        </strong>
                        {reg.entidade_id && (
                          <>
                            <br />
                            <small className="muted" style={{ fontFamily: 'monospace', fontSize: '0.75rem' }} title={reg.entidade_id}>
                              ID: {reg.entidade_id.length > 18 ? `${reg.entidade_id.slice(0, 8)}...` : reg.entidade_id}
                            </small>
                          </>
                        )}
                      </div>
                    ) : reg.entidade_id ? (
                      <span style={{ fontFamily: 'monospace', fontSize: '0.82rem', color: 'var(--muted)' }} title={reg.entidade_id}>
                        {reg.entidade_id.length > 24 ? `${reg.entidade_id.slice(0, 8)}...${reg.entidade_id.slice(-6)}` : reg.entidade_id}
                      </span>
                    ) : (
                      <span className="muted" style={{ fontStyle: 'italic' }}>—</span>
                    )}
                  </td>
                    <td style={{ padding: '12px 16px', fontSize: '0.85rem' }}>
                      {reg.autor_nome ? (
                        <div>
                          <strong>{reg.autor_nome}</strong>
                          {reg.autor_papel && (
                            <>
                              <br />
                              <small className="muted">{t(`papel.${reg.autor_papel}`, reg.autor_papel)}</small>
                            </>
                          )}
                        </div>
                      ) : reg.quem ? (
                        <span title={reg.quem} style={{ fontFamily: 'monospace', fontSize: '0.82rem' }}>
                          {reg.quem.slice(0, 8)}...
                        </span>
                      ) : (
                        <span className="muted" style={{ fontStyle: 'italic', fontSize: '0.82rem' }}>
                          {t('auditoria.autor_sistema')}
                        </span>
                      )}
                    </td>
                    <td style={{ padding: '12px 16px', fontSize: '0.85rem', color: 'var(--muted)' }}>
                      {reg.ip || '—'}
                    </td>
                    <td style={{ padding: '12px 16px', textAlign: 'center' }}>
                      <button
                        type="button"
                        className="btn btn-sm"
                        style={{ padding: '4px 10px', fontSize: '0.8rem' }}
                        onClick={() => {
                          setDetalheSelecionado(reg);
                          setAbaModal('amigavel');
                          setCopiado(false);
                        }}
                      >
                        {t('auditoria.btn_detalhes')}
                      </button>
                    </td>
                  </tr>
                ))
            )}
          </tbody>
        </table>
      </div>

      {/* Modal de Inspeção dos Payloads (com dados antes/depois sanitizados) */}
      {detalheSelecionado && (
        <div
          role="dialog"
          aria-modal="true"
          onClick={() => setDetalheSelecionado(null)}
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.65)',
            backdropFilter: 'blur(4px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 3000,
            padding: 16,
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              background: 'var(--card)',
              borderRadius: 16,
              border: '1px solid var(--line)',
              boxShadow: 'var(--shadow-pop)',
              width: '100%',
              maxWidth: 780,
              maxHeight: '90vh',
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden',
            }}
          >
            {/* Modal Header */}
            <div
              style={{
                padding: '16px 20px',
                borderBottom: '1px solid var(--line)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <div>
                <h3 style={{ margin: 0, fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                  <span>{t('auditoria.modal_titulo')}</span>
                  <span
                    style={{
                      fontSize: '0.82rem',
                      fontWeight: 600,
                      padding: '2px 8px',
                      borderRadius: 4,
                      background: 'var(--bg)',
                      color: 'var(--primary)',
                      border: '1px solid var(--line)',
                    }}
                  >
                    {t(`auditoria.operacoes.${detalheSelecionado.operacao}`, detalheSelecionado.operacao)}
                  </span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--muted)', fontFamily: 'monospace' }}>
                    ({detalheSelecionado.operacao})
                  </span>
                </h3>
                <p className="muted small" style={{ margin: '4px 0 0' }}>
                  {t('auditoria.modal_subtitulo')}
                </p>
              </div>
              <button
                type="button"
                className="btn btn-ghost"
                onClick={() => setDetalheSelecionado(null)}
                style={{ fontSize: '1.2rem', padding: '4px 8px' }}
                aria-label={t('auditoria.modal_fechar')}
              >
                ✕
              </button>
            </div>

            {/* Modal Tabs Navigation */}
            <div
              style={{
                display: 'flex',
                gap: 20,
                padding: '0 20px',
                borderBottom: '1px solid var(--line)',
                background: 'var(--card)',
              }}
            >
              <button
                type="button"
                onClick={() => setAbaModal('amigavel')}
                style={{
                  padding: '10px 4px',
                  background: 'none',
                  border: 'none',
                  borderBottom: abaModal === 'amigavel' ? '2px solid var(--primary)' : '2px solid transparent',
                  color: abaModal === 'amigavel' ? 'var(--primary)' : 'var(--muted)',
                  fontWeight: abaModal === 'amigavel' ? 600 : 500,
                  cursor: 'pointer',
                  fontSize: '0.88rem',
                }}
              >
                {t('auditoria.modal_visao_operacional')}
              </button>
              <button
                type="button"
                onClick={() => setAbaModal('json')}
                style={{
                  padding: '10px 4px',
                  background: 'none',
                  border: 'none',
                  borderBottom: abaModal === 'json' ? '2px solid var(--primary)' : '2px solid transparent',
                  color: abaModal === 'json' ? 'var(--primary)' : 'var(--muted)',
                  fontWeight: abaModal === 'json' ? 600 : 500,
                  cursor: 'pointer',
                  fontSize: '0.88rem',
                }}
              >
                {t('auditoria.modal_json_tecnico')}
              </button>
            </div>

            {/* Modal Body */}
            <div style={{ padding: '20px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 16 }}>
              {/* Metadados do Registro */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
                  gap: 12,
                  background: 'var(--bg)',
                  padding: 12,
                  borderRadius: 8,
                  border: '1px solid var(--line)',
                  fontSize: '0.85rem',
                }}
              >
                <div>
                  <span className="muted">{t('auditoria.coluna_quando')}:</span>
                  <div>{new Date(detalheSelecionado.quando).toLocaleString()}</div>
                </div>
                <div>
                  <span className="muted">{t('auditoria.coluna_entidade')}:</span>
                  <div>
                    <strong>{detalheSelecionado.entidade}</strong>
                    {detalheSelecionado.identificador_amigavel && (
                      <span style={{ color: 'var(--primary)', fontWeight: 600 }}> ({detalheSelecionado.identificador_amigavel})</span>
                    )}
                  </div>
                  {detalheSelecionado.entidade_id && (
                    <small className="muted" style={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                      ID: {detalheSelecionado.entidade_id}
                    </small>
                  )}
                </div>
                <div>
                  <span className="muted">{t('auditoria.coluna_autor')}:</span>
                  <div>
                    {detalheSelecionado.autor_nome ? (
                      <strong>
                        {detalheSelecionado.autor_nome}
                        {detalheSelecionado.autor_papel && ` (${t(`papel.${detalheSelecionado.autor_papel}`, detalheSelecionado.autor_papel)})`}
                      </strong>
                    ) : (
                      <span className="muted" style={{ fontStyle: 'italic' }}>
                        {t('auditoria.autor_sistema')}
                      </span>
                    )}
                  </div>
                  {detalheSelecionado.quem && (
                    <small className="muted" style={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                      UUID: {detalheSelecionado.quem}
                    </small>
                  )}
                </div>
                <div>
                  <span className="muted">{t('auditoria.coluna_ip')}:</span>
                  <div>{detalheSelecionado.ip || '—'}</div>
                </div>
              </div>

              {/* Aba 1: Visual Amigável */}
              {abaModal === 'amigavel' && (
                <div>
                  {temAntes && temDepois ? (
                    <div>
                      <h4 style={{ margin: '0 0 10px', fontSize: '0.9rem', color: 'var(--ink)' }}>
                        {t('auditoria.modal_mudanca_estado')}
                      </h4>
                      <div style={{ border: '1px solid var(--line)', borderRadius: 8, overflow: 'hidden' }}>
                        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.86rem' }}>
                          <thead>
                            <tr style={{ background: 'var(--bg)', borderBottom: '1px solid var(--line)' }}>
                              <th style={{ textAlign: 'left', padding: '10px 14px', width: '32%', color: 'var(--muted)' }}>
                                {t('auditoria.modal_campo')}
                              </th>
                              <th style={{ textAlign: 'left', padding: '10px 14px', width: '34%', color: 'var(--muted)' }}>
                                {t('auditoria.modal_anterior')}
                              </th>
                              <th style={{ textAlign: 'left', padding: '10px 14px', width: '34%', color: 'var(--muted)' }}>
                                {t('auditoria.modal_novo')}
                              </th>
                            </tr>
                          </thead>
                          <tbody>
                            {chavesComparacao.map((chave) => {
                              const valAntes = detalheSelecionado.dados_antes ? detalheSelecionado.dados_antes[chave] : undefined;
                              const valDepois = detalheSelecionado.dados_depois ? detalheSelecionado.dados_depois[chave] : undefined;
                              const mudou = JSON.stringify(valAntes) !== JSON.stringify(valDepois);

                              return (
                                <tr
                                  key={chave}
                                  style={{
                                    borderBottom: '1px solid var(--line)',
                                    background: mudou ? 'rgba(59, 130, 246, 0.04)' : undefined,
                                  }}
                                >
                                  <td style={{ padding: '10px 14px', verticalAlign: 'top' }}>
                                    <div style={{ fontWeight: 600, color: 'var(--ink)' }}>
                                      {t(`auditoria.campos.${chave}`, chave)}
                                    </div>
                                    <small className="muted" style={{ fontFamily: 'monospace', fontSize: '0.74rem' }}>
                                      {chave}
                                    </small>
                                  </td>
                                  <td style={{ padding: '10px 14px', verticalAlign: 'top' }}>
                                    {formatarValor(chave, valAntes)}
                                  </td>
                                  <td style={{ padding: '10px 14px', verticalAlign: 'top' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                                      {formatarValor(chave, valDepois)}
                                      {mudou && (
                                        <span
                                          style={{
                                            fontSize: '0.68rem',
                                            padding: '1px 6px',
                                            borderRadius: 4,
                                            background: 'rgba(16, 185, 129, 0.15)',
                                            color: '#10b981',
                                            fontWeight: 600,
                                            border: '1px solid rgba(16, 185, 129, 0.3)',
                                          }}
                                        >
                                          {t('auditoria.modal_alterado')}
                                        </span>
                                      )}
                                    </div>
                                  </td>
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  ) : temDepois ? (
                    <div>
                      <h4 style={{ margin: '0 0 10px', fontSize: '0.9rem', color: 'var(--ink)' }}>
                        {t('auditoria.modal_registro_inicial')}
                      </h4>
                      <div
                        style={{
                          display: 'grid',
                          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                          gap: 12,
                        }}
                      >
                        {Object.entries(detalheSelecionado.dados_depois || {}).map(([chave, val]) => (
                          <div
                            key={chave}
                            style={{
                              background: 'var(--bg)',
                              border: '1px solid var(--line)',
                              borderRadius: 8,
                              padding: '10px 14px',
                            }}
                          >
                            <div className="muted small" style={{ marginBottom: 4, display: 'flex', justifyContent: 'space-between' }}>
                              <span>{t(`auditoria.campos.${chave}`, chave)}</span>
                              <span style={{ fontFamily: 'monospace', fontSize: '0.72rem' }}>{chave}</span>
                            </div>
                            <div>{formatarValor(chave, val)}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : temAntes ? (
                    <div>
                      <h4 style={{ margin: '0 0 10px', fontSize: '0.9rem', color: 'var(--ink)' }}>
                        {t('auditoria.modal_anterior')}
                      </h4>
                      <div
                        style={{
                          display: 'grid',
                          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                          gap: 12,
                        }}
                      >
                        {Object.entries(detalheSelecionado.dados_antes || {}).map(([chave, val]) => (
                          <div
                            key={chave}
                            style={{
                              background: 'var(--bg)',
                              border: '1px solid var(--line)',
                              borderRadius: 8,
                              padding: '10px 14px',
                            }}
                          >
                            <div className="muted small" style={{ marginBottom: 4, display: 'flex', justifyContent: 'space-between' }}>
                              <span>{t(`auditoria.campos.${chave}`, chave)}</span>
                              <span style={{ fontFamily: 'monospace', fontSize: '0.72rem' }}>{chave}</span>
                            </div>
                            <div>{formatarValor(chave, val)}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div
                      style={{
                        textAlign: 'center',
                        padding: '32px 16px',
                        color: 'var(--muted)',
                        background: 'var(--bg)',
                        borderRadius: 8,
                        border: '1px solid var(--line)',
                      }}
                    >
                      {t('auditoria.modal_sem_alteracoes')}
                    </div>
                  )}
                </div>
              )}

              {/* Aba 2: JSON Técnico */}
              {abaModal === 'json' && (
                <div>
                  <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 12 }}>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={handleCopiarJson}
                      style={{ fontSize: '0.8rem' }}
                    >
                      {copiado ? (
                        <span style={{ color: 'var(--ok)' }}>✓ {t('auditoria.modal_copiado')}</span>
                      ) : (
                        t('auditoria.modal_copiar_json')
                      )}
                    </Button>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 16 }}>
                    <div>
                      <h4 style={{ margin: '0 0 6px', fontSize: '0.88rem', color: 'var(--muted)' }}>
                        {t('auditoria.modal_dados_antes')}
                      </h4>
                      {detalheSelecionado.dados_antes ? (
                        <pre
                          style={{
                            background: 'var(--bg)',
                            border: '1px solid var(--line)',
                            borderRadius: 8,
                            padding: 12,
                            fontSize: '0.82rem',
                            overflowX: 'auto',
                            maxHeight: 180,
                            color: 'var(--ink)',
                          }}
                        >
                          {JSON.stringify(detalheSelecionado.dados_antes, null, 2)}
                        </pre>
                      ) : (
                        <p className="muted small" style={{ fontStyle: 'italic', margin: 0 }}>
                          {t('auditoria.modal_sem_dados')}
                        </p>
                      )}
                    </div>

                    <div>
                      <h4 style={{ margin: '0 0 6px', fontSize: '0.88rem', color: 'var(--muted)' }}>
                        {t('auditoria.modal_dados_depois')}
                      </h4>
                      {detalheSelecionado.dados_depois ? (
                        <pre
                          style={{
                            background: 'var(--bg)',
                            border: '1px solid var(--line)',
                            borderRadius: 8,
                            padding: 12,
                            fontSize: '0.82rem',
                            overflowX: 'auto',
                            maxHeight: 180,
                            color: 'var(--ink)',
                          }}
                        >
                          {JSON.stringify(detalheSelecionado.dados_depois, null, 2)}
                        </pre>
                      ) : (
                        <p className="muted small" style={{ fontStyle: 'italic', margin: 0 }}>
                          {t('auditoria.modal_sem_dados')}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div
              style={{
                padding: '12px 20px',
                borderTop: '1px solid var(--line)',
                display: 'flex',
                justifyContent: 'flex-end',
              }}
            >
              <Button variant="secondary" size="sm" onClick={() => setDetalheSelecionado(null)}>
                {t('auditoria.modal_fechar')}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
