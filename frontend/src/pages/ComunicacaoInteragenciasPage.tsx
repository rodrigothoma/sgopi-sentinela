import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../hooks/useToast';
import { mensagemDeErro } from '../services/api';
import {
  interagenciasService,
  type Departamento,
  type ComunicacaoInteragencias,
} from '../services/interagenciasService';
import { formatarDataHora } from '../utils/datas';

const NOMES_DEPARTAMENTOS: Record<string, string> = {
  POLICIA_CIVIL: 'Polícia Civil',
  POLICIA_MILITAR: 'Polícia Militar',
  POLICIA_CIENTIFICA: 'Polícia Científica',
  DEFESA_CIVIL: 'Defesa Civil / Bombeiros',
  GUARDA_MUNICIPAL: 'Guarda Municipal',
  POLICIA_RODOVIARIA_FEDERAL: 'Polícia Rodoviária Federal',
};

const CORES_DEPARTAMENTOS: Record<string, { bg: string; color: string; border: string }> = {
  POLICIA_CIVIL: { bg: 'rgba(37, 99, 235, 0.12)', color: '#2563eb', border: 'rgba(37, 99, 235, 0.3)' },
  POLICIA_MILITAR: { bg: 'rgba(22, 101, 52, 0.12)', color: '#166534', border: 'rgba(22, 101, 52, 0.3)' },
  POLICIA_CIENTIFICA: { bg: 'rgba(147, 51, 234, 0.12)', color: '#9333ea', border: 'rgba(147, 51, 234, 0.3)' },
  DEFESA_CIVIL: { bg: 'rgba(234, 88, 12, 0.12)', color: '#ea580c', border: 'rgba(234, 88, 12, 0.3)' },
  GUARDA_MUNICIPAL: { bg: 'rgba(13, 148, 136, 0.12)', color: '#0d9488', border: 'rgba(13, 148, 136, 0.3)' },
  POLICIA_RODOVIARIA_FEDERAL: { bg: 'rgba(202, 138, 4, 0.12)', color: '#a16207', border: 'rgba(202, 138, 4, 0.3)' },
};

export const ComunicacaoInteragenciasPage: React.FC = () => {
  const { t } = useTranslation(['interagencias', 'common']);
  const { tem } = useAuth();
  const { avisar } = useToast();

  const podeDespachar = tem('DELEGADO', 'SUPERVISOR', 'ESCRIVAO', 'OPERADOR_CENTRAL');

  const [departamentos, setDepartamentos] = useState<Departamento[]>([]);
  const [comunicacoes, setComunicacoes] = useState<ComunicacaoInteragencias[]>([]);
  const [carregando, setCarregando] = useState(false);

  // Filtros
  const [filtroDept, setFiltroDept] = useState<string>('');
  const [filtroProtocolo, setFiltroProtocolo] = useState<string>('');

  // Mensagem selecionada para visualização de Thread
  const [selecionada, setSelecionada] = useState<ComunicacaoInteragencias | null>(null);

  // Modais e formulários
  const [modalNovoAberto, setModalNovoAberto] = useState(false);
  const [enviando, setEnviando] = useState(false);

  // Campos Novo Ofício
  const [origemNovo, setOrigemNovo] = useState<string>('POLICIA_CIVIL');
  const [destinatariosNovo, setDestinatariosNovo] = useState<string[]>([]);
  const [assuntoNovo, setAssuntoNovo] = useState('');
  const [corpoNovo, setCorpoNovo] = useState('');
  const [prioridadeNovo, setPrioridadeNovo] = useState('MEDIA');
  const [sigiloNovo, setSigiloNovo] = useState('PADRAO');
  const [protocoloNovo, setProtocoloNovo] = useState('');

  // Campos Resposta / Thread
  const [respostaOrigem, setRespostaOrigem] = useState<string>('POLICIA_CIVIL');
  const [respostaAssunto, setRespostaAssunto] = useState('');
  const [respostaCorpo, setRespostaCorpo] = useState('');
  const [respostaPrioridade, setRespostaPrioridade] = useState('MEDIA');
  const [respondendo, setRespondendo] = useState(false);

  const carregarDepartamentos = useCallback(async () => {
    try {
      const depts = await interagenciasService.listarDepartamentos();
      setDepartamentos(depts);
      if (depts.length > 0 && !origemNovo) {
        setOrigemNovo(depts[0].codigo);
      }
    } catch (err) {
      console.error('Erro ao listar departamentos:', err);
    }
  }, [origemNovo]);

  const carregarComunicacoes = useCallback(async () => {
    setCarregando(true);
    try {
      const dados = await interagenciasService.listar({
        departamento: filtroDept || undefined,
        protocolo: filtroProtocolo.trim() || undefined,
      });
      setComunicacoes(dados);
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    } finally {
      setCarregando(false);
    }
  }, [avisar, filtroDept, filtroProtocolo]);

  useEffect(() => {
    carregarDepartamentos();
  }, [carregarDepartamentos]);

  useEffect(() => {
    carregarComunicacoes();
  }, [carregarComunicacoes]);

  // Mensagens raiz (que não são respostas de outra)
  const mensagensRaiz = useMemo(() => {
    return comunicacoes.filter((c) => !c.mensagem_pai_id);
  }, [comunicacoes]);

  // Respostas da mensagem selecionada
  const respostasSelecionada = useMemo(() => {
    if (!selecionada) return [];
    return comunicacoes
      .filter((c) => c.mensagem_pai_id === selecionada.id)
      .sort((a, b) => new Date(a.criada_em).getTime() - new Date(b.criada_em).getTime());
  }, [comunicacoes, selecionada]);

  const handleToggleDestinatario = (codigo: string) => {
    setDestinatariosNovo((prev) =>
      prev.includes(codigo) ? prev.filter((c) => c !== codigo) : [...prev, codigo]
    );
  };

  const handleEnviarNovoOficio = async (e: React.FormEvent) => {
    e.preventDefault();
    if (destinatariosNovo.length === 0) {
      avisar(t('interagencias:validacao.selecione_destinatario', 'Selecione ao menos um departamento destinatário'), 'erro');
      return;
    }
    if (assuntoNovo.trim().length < 5) {
      avisar(t('interagencias:validacao.assunto_curto', 'O assunto deve ter no mínimo 5 caracteres'), 'erro');
      return;
    }
    if (corpoNovo.trim().length < 10) {
      avisar(t('interagencias:validacao.corpo_curto', 'O corpo deve ter no mínimo 10 caracteres'), 'erro');
      return;
    }

    setEnviando(true);
    try {
      const res = await interagenciasService.enviar({
        departamento_origem: origemNovo,
        departamentos_destinatarios: destinatariosNovo,
        assunto: assuntoNovo.trim(),
        corpo: corpoNovo.trim(),
        prioridade: prioridadeNovo,
        nivel_sigilo: sigiloNovo,
        protocolo_ocorrencia: protocoloNovo.trim() || null,
      });

      avisar(
        t('interagencias:sucesso_envio', {
          numero: res.numero_oficio,
          defaultValue: `Ofício ${res.numero_oficio} despachado com sucesso!`,
        }),
        'sucesso'
      );

      setModalNovoAberto(false);
      setAssuntoNovo('');
      setCorpoNovo('');
      setDestinatariosNovo([]);
      setProtocoloNovo('');
      await carregarComunicacoes();
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    } finally {
      setEnviando(false);
    }
  };

  const handleEnviarResposta = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selecionada) return;
    if (respostaAssunto.trim().length < 5) {
      avisar(t('interagencias:validacao.assunto_curto', 'O assunto deve ter no mínimo 5 caracteres'), 'erro');
      return;
    }
    if (respostaCorpo.trim().length < 10) {
      avisar(t('interagencias:validacao.corpo_curto', 'O corpo deve ter no mínimo 10 caracteres'), 'erro');
      return;
    }

    setRespondendo(true);
    try {
      const res = await interagenciasService.responder(selecionada.id, {
        departamento_origem: respostaOrigem,
        assunto: respostaAssunto.trim(),
        corpo: respostaCorpo.trim(),
        prioridade: respostaPrioridade,
      });

      avisar(
        t('interagencias:sucesso_resposta', {
          numero: res.numero_oficio,
          defaultValue: `Despacho ${res.numero_oficio} anexado à thread!`,
        }),
        'sucesso'
      );

      setRespostaCorpo('');
      setRespostaAssunto('');
      await carregarComunicacoes();
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    } finally {
      setRespondendo(false);
    }
  };

  const renderBadgeDept = (codigo: string) => {
    const nome = NOMES_DEPARTAMENTOS[codigo] || codigo;
    const estilo = CORES_DEPARTAMENTOS[codigo] || { bg: 'rgba(0,0,0,0.06)', color: 'var(--ink)', border: 'var(--line)' };
    return (
      <span
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          padding: '2px 8px',
          borderRadius: '4px',
          fontSize: '0.75rem',
          fontWeight: 600,
          background: estilo.bg,
          color: estilo.color,
          border: `1px solid ${estilo.border}`,
        }}
      >
        {nome}
      </span>
    );
  };

  const renderBadgePrioridade = (prioridade: string) => {
    const cor =
      prioridade === 'URGENTE'
        ? 'var(--danger)'
        : prioridade === 'ALTA'
          ? 'var(--warn)'
          : prioridade === 'MEDIA'
            ? 'var(--primary)'
            : 'var(--muted)';
    return (
      <span
        style={{
          fontSize: '0.72rem',
          fontWeight: 700,
          padding: '2px 6px',
          borderRadius: '4px',
          border: `1px solid ${cor}`,
          color: cor,
        }}
      >
        {prioridade}
      </span>
    );
  };

  return (
    <div style={{ padding: '1.5rem', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Topo da Página */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '1.75rem', fontWeight: 700, color: 'var(--ink)' }}>
            🏛️ {t('interagencias:titulo', 'Comunicação Interagências')}
          </h1>
          <p style={{ margin: '0.25rem 0 0', color: 'var(--muted)' }}>
            {t(
              'interagencias:subtitulo',
              'Despacho e tramitação oficial entre órgãos de Segurança Pública (Ofícios OFI-YYYY-XXXXXX)'
            )}
          </p>
        </div>
        {podeDespachar && (
          <button
            className="btn btn-primary"
            onClick={() => {
              setAssuntoNovo('');
              setCorpoNovo('');
              setDestinatariosNovo([]);
              setProtocoloNovo('');
              setModalNovoAberto(true);
            }}
            style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', height: '42px', padding: '0.6rem 1.2rem' }}
          >
            <span>✍️</span> {t('interagencias:btn_novo_oficio', 'Novo Ofício Interagências')}
          </button>
        )}
      </div>

      {/* Grid de Departamentos Oficiais (Filtro Rápido) */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '0.75rem', marginBottom: '1.25rem' }}>
        {departamentos.map((d) => {
          const ativo = filtroDept === d.codigo;
          const estilo = CORES_DEPARTAMENTOS[d.codigo] || { bg: 'transparent', color: 'var(--ink)', border: 'var(--line)' };
          return (
            <button
              key={d.codigo}
              type="button"
              onClick={() => setFiltroDept(ativo ? '' : d.codigo)}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'flex-start',
                padding: '0.75rem 1rem',
                borderRadius: '8px',
                border: `1.5px solid ${ativo ? estilo.color : 'var(--line)'}`,
                background: ativo ? estilo.bg : 'var(--card)',
                cursor: 'pointer',
                textAlign: 'left',
                transition: 'all 0.15s ease',
              }}
            >
              <span style={{ fontWeight: 700, fontSize: '0.86rem', color: estilo.color }}>{d.nome}</span>
              <span style={{ fontSize: '0.72rem', color: 'var(--muted)', marginTop: '2px', lineHeight: 1.3 }}>
                {d.descricao}
              </span>
            </button>
          );
        })}
      </div>

      {/* Barra de Filtros */}
      <div
        style={{
          display: 'flex',
          gap: '1rem',
          alignItems: 'center',
          marginBottom: '1.25rem',
          background: 'var(--card)',
          padding: '0.85rem 1rem',
          borderRadius: '8px',
          border: '1px solid var(--line)',
          flexWrap: 'wrap',
        }}
      >
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flex: 1, minWidth: '240px' }}>
          <span className="muted small">🔍</span>
          <input
            type="text"
            className="input-text"
            placeholder={t('interagencias:busca_protocolo', 'Filtrar por protocolo de ocorrência...')}
            value={filtroProtocolo}
            onChange={(e) => setFiltroProtocolo(e.target.value)}
            style={{ width: '100%', padding: '0.5rem 0.75rem', borderRadius: '6px', border: '1px solid var(--line)' }}
          />
        </div>

        {filtroDept && (
          <button
            type="button"
            className="btn btn-sm btn-ghost"
            onClick={() => setFiltroDept('')}
          >
            ✕ Limpar filtro: {NOMES_DEPARTAMENTOS[filtroDept] || filtroDept}
          </button>
        )}

        <button type="button" className="btn btn-sm btn-outline" onClick={carregarComunicacoes}>
          🔄 {t('actions.atualizar', 'Atualizar')}
        </button>
      </div>

      {/* Conteúdo Principal: Tabela de Ofícios e Drawer Lateral de Thread */}
      <div style={{ display: 'grid', gridTemplateColumns: selecionada ? '1fr 420px' : '1fr', gap: '1.25rem' }}>
        {/* Lista de Comunicações */}
        <div style={{ background: 'var(--card)', borderRadius: '8px', border: '1px solid var(--line)', overflow: 'hidden' }}>
          {carregando ? (
            <p style={{ textAlign: 'center', padding: '3rem', color: 'var(--muted)' }}>
              {t('actions.loading', 'Carregando comunicações...')}
            </p>
          ) : mensagensRaiz.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '3.5rem 1rem', color: 'var(--muted)' }}>
              <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>📭</div>
              <p style={{ margin: 0 }}>{t('interagencias:vazio', 'Nenhuma comunicação interagências encontrada.')}</p>
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table className="tabela" style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ background: 'var(--bg-surface)', borderBottom: '1px solid var(--line)', textAlign: 'left' }}>
                    <th style={{ padding: '0.75rem 1rem', fontSize: '0.82rem' }}>{t('interagencias:col_oficio', 'Ofício')}</th>
                    <th style={{ padding: '0.75rem 1rem', fontSize: '0.82rem' }}>{t('interagencias:col_origem', 'Origem')}</th>
                    <th style={{ padding: '0.75rem 1rem', fontSize: '0.82rem' }}>{t('interagencias:col_destinatarios', 'Destinatários')}</th>
                    <th style={{ padding: '0.75rem 1rem', fontSize: '0.82rem' }}>{t('interagencias:col_assunto', 'Assunto')}</th>
                    <th style={{ padding: '0.75rem 1rem', fontSize: '0.82rem' }}>{t('interagencias:col_prioridade', 'Prioridade')}</th>
                    <th style={{ padding: '0.75rem 1rem', fontSize: '0.82rem' }}>{t('interagencias:col_data', 'Data/Hora')}</th>
                    <th style={{ padding: '0.75rem 1rem', fontSize: '0.82rem', textAlign: 'right' }}>{t('interagencias:col_acoes', 'Ações')}</th>
                  </tr>
                </thead>
                <tbody>
                  {mensagensRaiz.map((m) => {
                    const isSelected = selecionada?.id === m.id;
                    const totalRespostas = comunicacoes.filter((c) => c.mensagem_pai_id === m.id).length;
                    return (
                      <tr
                        key={m.id}
                        style={{
                          borderBottom: '1px solid var(--line)',
                          background: isSelected ? 'var(--bg-hover, rgba(37, 99, 235, 0.05))' : 'transparent',
                          cursor: 'pointer',
                        }}
                        onClick={() => {
                          setSelecionada(m);
                          setRespostaAssunto(`Re: ${m.assunto}`);
                          setRespostaOrigem(m.departamentos_destinatarios[0] || 'POLICIA_CIVIL');
                        }}
                      >
                        <td style={{ padding: '0.75rem 1rem', fontWeight: 700, color: 'var(--primary)' }}>
                          {m.numero_oficio}
                          {m.protocolo_ocorrencia && (
                            <div style={{ fontSize: '0.72rem', color: 'var(--muted)', fontWeight: 400 }}>
                              Proc: {m.protocolo_ocorrencia}
                            </div>
                          )}
                        </td>
                        <td style={{ padding: '0.75rem 1rem' }}>{renderBadgeDept(m.departamento_origem)}</td>
                        <td style={{ padding: '0.75rem 1rem' }}>
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                            {m.departamentos_destinatarios.map((d) => (
                              <React.Fragment key={d}>{renderBadgeDept(d)}</React.Fragment>
                            ))}
                          </div>
                        </td>
                        <td style={{ padding: '0.75rem 1rem' }}>
                          <div style={{ fontWeight: 600, color: 'var(--ink)' }}>{m.assunto}</div>
                          <div style={{ fontSize: '0.78rem', color: 'var(--muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '300px' }}>
                            {m.corpo}
                          </div>
                        </td>
                        <td style={{ padding: '0.75rem 1rem' }}>{renderBadgePrioridade(m.prioridade)}</td>
                        <td style={{ padding: '0.75rem 1rem', fontSize: '0.8rem', color: 'var(--muted)', whiteSpace: 'nowrap' }}>
                          {formatarDataHora(m.criada_em)}
                        </td>
                        <td style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>
                          <button
                            type="button"
                            className="btn btn-sm btn-outline"
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelecionada(m);
                              setRespostaAssunto(`Re: ${m.assunto}`);
                              setRespostaOrigem(m.departamentos_destinatarios[0] || 'POLICIA_CIVIL');
                            }}
                          >
                            💬 {totalRespostas > 0 ? `${totalRespostas} respostas` : 'Ver / Responder'}
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Drawer Lateral de Thread / Detalhes */}
        {selecionada && (
          <aside
            style={{
              background: 'var(--card)',
              borderRadius: '8px',
              border: '1px solid var(--line)',
              padding: '1.25rem',
              display: 'flex',
              flexDirection: 'column',
              maxHeight: '800px',
              overflowY: 'auto',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem', borderBottom: '1px solid var(--line)', paddingBottom: '0.75rem' }}>
              <div>
                <span style={{ fontWeight: 700, fontSize: '1.1rem', color: 'var(--primary)' }}>
                  {selecionada.numero_oficio}
                </span>
                <h3 style={{ margin: '4px 0 0', fontSize: '1rem', color: 'var(--ink)' }}>{selecionada.assunto}</h3>
              </div>
              <button
                type="button"
                className="btn btn-sm btn-ghost"
                onClick={() => setSelecionada(null)}
                title="Fechar painel de thread"
              >
                ✕
              </button>
            </div>

            {/* Mensagem Inicial */}
            <div
              style={{
                background: 'var(--bg-surface)',
                borderRadius: '8px',
                padding: '1rem',
                border: '1px solid var(--line)',
                marginBottom: '1rem',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', flexWrap: 'wrap', gap: '4px' }}>
                <div>
                  <span className="muted small">De:</span> {renderBadgeDept(selecionada.departamento_origem)}
                </div>
                <span className="muted small">{formatarDataHora(selecionada.criada_em)}</span>
              </div>
              <div style={{ marginBottom: '0.5rem' }}>
                <span className="muted small">Para:</span>{' '}
                {selecionada.departamentos_destinatarios.map((d) => (
                  <span key={d} style={{ marginRight: '4px' }}>{renderBadgeDept(d)}</span>
                ))}
              </div>
              {selecionada.protocolo_ocorrencia && (
                <div style={{ fontSize: '0.78rem', color: 'var(--primary)', marginBottom: '0.5rem' }}>
                  Boletim Relacionado: <strong>{selecionada.protocolo_ocorrencia}</strong>
                </div>
              )}
              <div style={{ fontSize: '0.88rem', color: 'var(--ink)', lineHeight: 1.5, whiteSpace: 'pre-wrap' }}>
                {selecionada.corpo}
              </div>
            </div>

            {/* Lista de Respostas / Despachos da Thread */}
            {respostasSelecionada.length > 0 && (
              <div style={{ marginBottom: '1rem' }}>
                <h4 style={{ margin: '0 0 0.5rem', fontSize: '0.88rem', color: 'var(--muted)' }}>
                  Respostas e Encaminhamentos ({respostasSelecionada.length})
                </h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  {respostasSelecionada.map((r) => (
                    <div
                      key={r.id}
                      style={{
                        background: 'var(--card)',
                        border: '1px solid var(--line)',
                        borderRadius: '6px',
                        padding: '0.85rem',
                        borderLeft: `3px solid ${CORES_DEPARTAMENTOS[r.departamento_origem]?.color || 'var(--primary)'}`,
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                        <span style={{ fontWeight: 700, fontSize: '0.82rem', color: 'var(--ink)' }}>{r.numero_oficio}</span>
                        <span className="muted small">{formatarDataHora(r.criada_em)}</span>
                      </div>
                      <div style={{ marginBottom: '4px' }}>{renderBadgeDept(r.departamento_origem)}</div>
                      <div style={{ fontSize: '0.85rem', color: 'var(--ink)', lineHeight: 1.4, whiteSpace: 'pre-wrap' }}>
                        {r.corpo}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Formulário de Resposta */}
            {podeDespachar && (
              <form onSubmit={handleEnviarResposta} style={{ marginTop: 'auto', borderTop: '1px solid var(--line)', paddingTop: '1rem', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <h4 style={{ margin: 0, fontSize: '0.9rem', color: 'var(--ink)' }}>✍️ Responder na Thread</h4>
                <label>
                  <span className="muted small">Departamento Respondente</span>
                  <select
                    className="input-select"
                    value={respostaOrigem}
                    onChange={(e) => setRespostaOrigem(e.target.value)}
                    style={{ width: '100%', padding: '0.45rem', marginTop: '2px' }}
                  >
                    {departamentos.map((d) => (
                      <option key={d.codigo} value={d.codigo}>
                        {d.nome}
                      </option>
                    ))}
                  </select>
                </label>

                <label>
                  <span className="muted small">Assunto</span>
                  <input
                    type="text"
                    required
                    className="input-text"
                    value={respostaAssunto}
                    onChange={(e) => setRespostaAssunto(e.target.value)}
                    style={{ width: '100%', padding: '0.45rem', marginTop: '2px' }}
                  />
                </label>

                <label>
                  <span className="muted small">Prioridade</span>
                  <select
                    className="input-select"
                    value={respostaPrioridade}
                    onChange={(e) => setRespostaPrioridade(e.target.value)}
                    style={{ width: '100%', padding: '0.45rem', marginTop: '2px' }}
                  >
                    <option value="BAIXA">Baixa</option>
                    <option value="MEDIA">Média</option>
                    <option value="ALTA">Alta</option>
                    <option value="URGENTE">🔴 Urgente</option>
                  </select>
                </label>

                <label>
                  <span className="muted small">Despacho / Conteúdo</span>
                  <textarea
                    required
                    rows={3}
                    className="input-text"
                    placeholder="Digite a réplica oficial do departamento..."
                    value={respostaCorpo}
                    onChange={(e) => setRespostaCorpo(e.target.value)}
                    style={{ width: '100%', padding: '0.45rem', marginTop: '2px' }}
                  />
                </label>

                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={respondendo}
                  style={{ alignSelf: 'flex-end', marginTop: '4px' }}
                >
                  {respondendo ? t('actions.salvando', 'Despachando...') : t('interagencias:btn_responder', 'Enviar Despacho')}
                </button>
              </form>
            )}
          </aside>
        )}
      </div>

      {/* Modal Novo Ofício Interagências */}
      {modalNovoAberto && (
        <div
          className="modal-backdrop"
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.6)',
            backdropFilter: 'blur(4px)',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            zIndex: 1200,
          }}
          onClick={() => setModalNovoAberto(false)}
        >
          <div
            style={{
              background: 'var(--card)',
              color: 'var(--ink)',
              padding: '1.5rem',
              borderRadius: '12px',
              border: '1px solid var(--line)',
              maxWidth: '620px',
              width: '90%',
              maxHeight: '90vh',
              overflowY: 'auto',
              boxShadow: 'var(--shadow-pop)',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h2 style={{ marginTop: 0, color: 'var(--ink)' }}>
              🏛️ {t('interagencias:modal_novo.titulo', 'Novo Ofício Interagências')}
            </h2>
            <p style={{ color: 'var(--muted)', fontSize: '0.9rem', marginTop: '-0.5rem', marginBottom: '1.25rem' }}>
              {t(
                'interagencias:modal_novo.subtitulo',
                'Emissão formal de ofício com numeração sequencial OFI-YYYY-XXXXXX para integração de Segurança Pública.'
              )}
            </p>

            <form onSubmit={handleEnviarNovoOficio} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <label>
                  <strong>{t('interagencias:modal_novo.origem', 'Órgão de Origem')}</strong>
                  <select
                    className="input-select"
                    value={origemNovo}
                    onChange={(e) => setOrigemNovo(e.target.value)}
                    style={{ width: '100%', padding: '0.6rem', marginTop: '4px' }}
                  >
                    {departamentos.map((d) => (
                      <option key={d.codigo} value={d.codigo}>
                        {d.nome}
                      </option>
                    ))}
                  </select>
                </label>

                <label>
                  <strong>{t('interagencias:modal_novo.prioridade', 'Prioridade')}</strong>
                  <select
                    className="input-select"
                    value={prioridadeNovo}
                    onChange={(e) => setPrioridadeNovo(e.target.value)}
                    style={{ width: '100%', padding: '0.6rem', marginTop: '4px' }}
                  >
                    <option value="BAIXA">Baixa</option>
                    <option value="MEDIA">Média (Padrão)</option>
                    <option value="ALTA">Alta</option>
                    <option value="URGENTE">🔴 Urgente</option>
                  </select>
                </label>
              </div>

              <div>
                <strong style={{ display: 'block', marginBottom: '6px' }}>
                  {t('interagencias:modal_novo.destinatarios', 'Órgãos Destinatários (ao menos um)')}
                </strong>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '8px' }}>
                  {departamentos
                    .filter((d) => d.codigo !== origemNovo)
                    .map((d) => {
                      const selecionado = destinatariosNovo.includes(d.codigo);
                      return (
                        <label
                          key={d.codigo}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px',
                            padding: '8px 10px',
                            borderRadius: '6px',
                            border: `1px solid ${selecionado ? 'var(--primary)' : 'var(--line)'}`,
                            background: selecionado ? 'rgba(37, 99, 235, 0.08)' : 'var(--bg-surface)',
                            cursor: 'pointer',
                            fontSize: '0.85rem',
                          }}
                        >
                          <input
                            type="checkbox"
                            checked={selecionado}
                            onChange={() => handleToggleDestinatario(d.codigo)}
                          />
                          <span>{d.nome}</span>
                        </label>
                      );
                    })}
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '12px' }}>
                <label>
                  <strong>{t('interagencias:modal_novo.sigilo', 'Grau de Sigilo')}</strong>
                  <select
                    className="input-select"
                    value={sigiloNovo}
                    onChange={(e) => setSigiloNovo(e.target.value)}
                    style={{ width: '100%', padding: '0.6rem', marginTop: '4px' }}
                  >
                    <option value="PADRAO">Padrão / Ostensivo</option>
                    <option value="RESTRITO">Restrito</option>
                    <option value="CONFIDENCIAL">🔒 Confidencial</option>
                  </select>
                </label>

                <label>
                  <strong>{t('interagencias:modal_novo.protocolo', 'Protocolo Vinculado')}</strong>
                  <input
                    type="text"
                    className="input-text"
                    placeholder="Ex: 20261003-0001"
                    value={protocoloNovo}
                    onChange={(e) => setProtocoloNovo(e.target.value)}
                    style={{ width: '100%', padding: '0.6rem', marginTop: '4px' }}
                  />
                </label>
              </div>

              <label>
                <strong>{t('interagencias:modal_novo.assunto', 'Assunto do Ofício')}</strong>
                <input
                  type="text"
                  required
                  className="input-text"
                  placeholder="Ex: Solicitação de Perícia Balística Complementar"
                  value={assuntoNovo}
                  onChange={(e) => setAssuntoNovo(e.target.value)}
                  style={{ width: '100%', padding: '0.6rem', marginTop: '4px' }}
                />
              </label>

              <label>
                <strong>{t('interagencias:modal_novo.corpo', 'Texto / Despacho do Ofício')}</strong>
                <textarea
                  required
                  rows={5}
                  className="input-text"
                  placeholder="Descreva a solicitação oficial, elementos de fato e providências requeridas do órgão de destino..."
                  value={corpoNovo}
                  onChange={(e) => setCorpoNovo(e.target.value)}
                  style={{ width: '100%', padding: '0.6rem', marginTop: '4px' }}
                />
              </label>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem', marginTop: '8px' }}>
                <button
                  type="button"
                  className="btn btn-ghost"
                  onClick={() => setModalNovoAberto(false)}
                  style={{ height: '42px' }}
                >
                  {t('actions.cancelar', 'Cancelar')}
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={enviando}
                  style={{ height: '42px', padding: '0 1.5rem' }}
                >
                  {enviando ? t('actions.salvando', 'Despachando...') : t('interagencias:btn_despachar', 'Despachar Ofício')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default ComunicacaoInteragenciasPage;
