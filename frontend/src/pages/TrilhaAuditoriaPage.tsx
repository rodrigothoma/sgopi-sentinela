import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { GlideSelect, GlideSelectOption } from '../components/common/GlideSelect';
import { Button } from '../components/common/Button';
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
  'evidencia.acessar',
];

const ENTIDADES: string[] = [
  'Ocorrencia',
  'Viatura',
  'OrdemDespacho',
  'Evidencia',
  'Usuario',
];

function getBadgeCor(operacao: string): { bg: string; color: string; border: string } {
  if (operacao.includes('rejeitar') || operacao.includes('negado')) {
    return { bg: 'rgba(239, 68, 68, 0.15)', color: '#ef4444', border: 'rgba(239, 68, 68, 0.3)' };
  }
  if (operacao.includes('validar') || operacao.includes('registrar')) {
    return { bg: 'rgba(16, 185, 129, 0.15)', color: '#10b981', border: 'rgba(16, 185, 129, 0.3)' };
  }
  if (operacao.includes('devolver') || operacao.includes('corrigir') || operacao.includes('alterar')) {
    return { bg: 'rgba(245, 158, 11, 0.15)', color: '#f59e0b', border: 'rgba(245, 158, 11, 0.3)' };
  }
  return { bg: 'rgba(59, 130, 246, 0.15)', color: '#3b82f6', border: 'rgba(59, 130, 246, 0.3)' };
}

/**
 * Painel de Trilha de Auditoria Imutável (RF20 / RNF02 / RNF03).
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
      const matchId = r.entidade_id.toLowerCase().includes(termo);
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
              registrosFiltrados.map((reg) => {
                const corBadge = getBadgeCor(reg.operacao);
                return (
                  <tr key={reg.id} style={{ borderBottom: '1px solid var(--line)' }}>
                    <td style={{ padding: '12px 16px', whiteSpace: 'nowrap', fontSize: '0.85rem' }}>
                      <strong>{new Date(reg.quando).toLocaleDateString()}</strong>
                      <br />
                      <span className="muted">{new Date(reg.quando).toLocaleTimeString()}</span>
                    </td>
                    <td style={{ padding: '12px 16px' }}>
                      <span
                        style={{
                          display: 'inline-block',
                          padding: '4px 9px',
                          borderRadius: 6,
                          fontSize: '0.82rem',
                          fontWeight: 600,
                          backgroundColor: corBadge.bg,
                          color: corBadge.color,
                          border: `1px solid ${corBadge.border}`,
                        }}
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
                          <br />
                          <small className="muted" style={{ fontFamily: 'monospace', fontSize: '0.75rem' }} title={reg.entidade_id}>
                            ID: {reg.entidade_id.length > 18 ? `${reg.entidade_id.slice(0, 8)}...` : reg.entidade_id}
                          </small>
                        </div>
                      ) : (
                        <span style={{ fontFamily: 'monospace', fontSize: '0.82rem', color: 'var(--muted)' }} title={reg.entidade_id}>
                          {reg.entidade_id.length > 24 ? `${reg.entidade_id.slice(0, 8)}...${reg.entidade_id.slice(-6)}` : reg.entidade_id}
                        </span>
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
                        onClick={() => setDetalheSelecionado(reg)}
                      >
                        {t('auditoria.btn_detalhes')}
                      </button>
                    </td>
                  </tr>
                );
              })
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
              maxWidth: 720,
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
                  <small className="muted" style={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                    ID: {detalheSelecionado.entidade_id}
                  </small>
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

              {/* Payloads Antes e Depois */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 16 }}>
                <div>
                  <h4 style={{ margin: '0 0 6px', fontSize: '0.9rem', color: 'var(--muted)' }}>
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
                  <h4 style={{ margin: '0 0 6px', fontSize: '0.9rem', color: 'var(--muted)' }}>
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
