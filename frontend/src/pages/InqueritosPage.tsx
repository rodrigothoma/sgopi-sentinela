import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../hooks/useToast';
import { mensagemDeErro } from '../services/api';
import {
  inqueritosService,
  type Inquerito,
  type ConexaoSugerida,
} from '../services/inqueritosService';
import { ocorrenciasService } from '../services/ocorrenciasService';
import { type OcorrenciaResumo } from '../types/api';
import { SpringCheck } from '../components/common/SpringCheck';
import { GlideSelect, type GlideSelectOption } from '../components/common/GlideSelect';

const ITENS_POR_PAGINA = 10;

export const InqueritosPage: React.FC = () => {
  const { t } = useTranslation(['inqueritos', 'common']);
  const { tem } = useAuth();
  const { avisar } = useToast();

  const [inqueritos, setInqueritos] = useState<Inquerito[]>([]);
  const [total, setTotal] = useState(0);
  const [filtroStatus, setFiltroStatus] = useState<string>('TODOS');
  const [carregando, setCarregando] = useState(false);

  // Inquérito selecionado para ver detalhes
  const [selecionado, setSelecionado] = useState<Inquerito | null>(null);

  // Modais
  const [modalInstaurarAberto, setModalInstaurarAberto] = useState(false);
  const [modalConcluirAberto, setModalConcluirAberto] = useState(false);
  const [modalVincularAberto, setModalVincularAberto] = useState(false);

  // Formulários
  const [ementa, setEmenta] = useState('');
  const [relatorioFinal, setRelatorioFinal] = useState('');
  const [ocorrenciasValidadas, setOcorrenciasValidadas] = useState<OcorrenciaResumo[]>([]);
  const [ocorrenciasSelecionadasIds, setOcorrenciasSelecionadasIds] = useState<string[]>([]);
  const [ocorrenciaPrincipalId, setOcorrenciaPrincipalId] = useState<string | null>(null);

  // Paginação e busca no modal de instauração
  const [paginaInstaurar, setPaginaInstaurar] = useState<number>(1);
  const [buscaInstaurar, setBuscaInstaurar] = useState<string>('');
  const [inputManualId, setInputManualId] = useState<string>('');
  const [buscandoManual, setBuscandoManual] = useState<boolean>(false);

  // Paginação e busca no modal de vinculação
  const [paginaVincular, setPaginaVincular] = useState<number>(1);
  const [buscaVincular, setBuscaVincular] = useState<string>('');
  const [inputManualVincularId, setInputManualVincularId] = useState<string>('');
  const [buscandoManualVincular, setBuscandoManualVincular] = useState<boolean>(false);

  // Motor de sugestão de conexões
  const [sugestoes, setSugestoes] = useState<ConexaoSugerida[]>([]);
  const [carregandoSugestoes, setCarregandoSugestoes] = useState(false);

  const opcoesStatusInquerito: GlideSelectOption[] = useMemo(
    () => [
      { value: 'TODOS', label: t('inqueritos:filtros.todos') },
      { value: 'EM_ANDAMENTO', label: t('inqueritos:filtros.em_andamento') },
      { value: 'CONCLUIDO', label: t('inqueritos:filtros.concluidos') },
      { value: 'ARQUIVADO', label: t('inqueritos:filtros.arquivados') },
    ],
    [t],
  );

  const carregarInqueritos = useCallback(async () => {
    setCarregando(true);
    try {
      const statusParam = filtroStatus === 'TODOS' ? undefined : [filtroStatus];
      const res = await inqueritosService.listar({ status: statusParam });
      setInqueritos(res.itens);
      setTotal(res.total);
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    } finally {
      setCarregando(false);
    }
  }, [filtroStatus, avisar]);

  useEffect(() => {
    carregarInqueritos();
  }, [carregarInqueritos]);

  const carregarValidadas = async () => {
    try {
      const res = await ocorrenciasService.listar(['VALIDADA'], 100);
      setOcorrenciasValidadas(res.itens);
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    }
  };

  const abrirModalInstaurar = () => {
    setEmenta('');
    setOcorrenciasSelecionadasIds([]);
    setOcorrenciaPrincipalId(null);
    setPaginaInstaurar(1);
    setBuscaInstaurar('');
    setInputManualId('');
    carregarValidadas();
    setModalInstaurarAberto(true);
  };

  const abrirModalVincular = () => {
    setPaginaVincular(1);
    setBuscaVincular('');
    setInputManualVincularId('');
    carregarValidadas();
    setModalVincularAberto(true);
  };

  const executarInstauracao = async (e: React.FormEvent) => {
    e.preventDefault();
    if (ementa.trim().length < 10) {
      avisar(t('inqueritos:validacoes.ementa_min'), 'erro');
      return;
    }

    // Ordena as ocorrências selecionadas de modo que o Fato Principal seja o primeiro elemento (index 0)
    const listaOrdenada: string[] = [];
    if (ocorrenciaPrincipalId && ocorrenciasSelecionadasIds.includes(ocorrenciaPrincipalId)) {
      listaOrdenada.push(ocorrenciaPrincipalId);
    }
    for (const id of ocorrenciasSelecionadasIds) {
      if (id !== ocorrenciaPrincipalId) {
        listaOrdenada.push(id);
      }
    }

    try {
      await inqueritosService.instaurar({
        ementa: ementa.trim(),
        ocorrencias_iniciais_ids: listaOrdenada,
      });
      avisar(t('inqueritos:notificacoes.instaurado_sucesso'), 'sucesso');
      setModalInstaurarAberto(false);
      carregarInqueritos();
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    }
  };

  const adicionarOcorrenciaManual = async () => {
    const termo = inputManualId.trim();
    if (!termo) return;

    // 1. Procura se já está na lista local por protocolo ou ID
    const encontrada = ocorrenciasValidadas.find(
      (oc) =>
        oc.ocorrencia_id.toLowerCase() === termo.toLowerCase() ||
        oc.numero_protocolo.toLowerCase() === termo.toLowerCase(),
    );

    if (encontrada) {
      if (!ocorrenciasSelecionadasIds.includes(encontrada.ocorrencia_id)) {
        setOcorrenciasSelecionadasIds((prev) => [...prev, encontrada.ocorrencia_id]);
        if (!ocorrenciaPrincipalId) {
          setOcorrenciaPrincipalId(encontrada.ocorrencia_id);
        }
        avisar(`Ocorrência ${encontrada.numero_protocolo} adicionada à seleção.`, 'sucesso');
      } else {
        avisar(`Ocorrência ${encontrada.numero_protocolo} já está selecionada.`, 'info');
      }
      setInputManualId('');
      return;
    }

    // 2. Se for formato UUID, tenta buscar no servidor
    const isUuid = /^[0-9a-fA-F-]{32,36}$/.test(termo);
    if (isUuid) {
      setBuscandoManual(true);
      try {
        const detalhe = await ocorrenciasService.buscarPorId(termo);
        const novoResumo: OcorrenciaResumo = {
          ocorrencia_id: detalhe.ocorrencia_id,
          numero_protocolo: detalhe.numero_protocolo,
          natureza: detalhe.natureza,
          localizacao: detalhe.localizacao,
          latitude: detalhe.latitude,
          longitude: detalhe.longitude,
          status: detalhe.status,
          data_hora_fato: detalhe.data_hora_fato,
          criada_em: detalhe.criada_em,
          atualizada_em: detalhe.atualizada_em,
          agente_policial_id: detalhe.agente_policial_id,
          versao: detalhe.versao,
        };
        setOcorrenciasValidadas((prev) => [novoResumo, ...prev.filter((o) => o.ocorrencia_id !== novoResumo.ocorrencia_id)]);
        setOcorrenciasSelecionadasIds((prev) => [...prev, novoResumo.ocorrencia_id]);
        if (!ocorrenciaPrincipalId) {
          setOcorrenciaPrincipalId(novoResumo.ocorrencia_id);
        }
        avisar(`Ocorrência ${novoResumo.numero_protocolo} localizada e adicionada!`, 'sucesso');
        setInputManualId('');
      } catch (err) {
        avisar(mensagemDeErro(err, 'Ocorrência não encontrada com o ID informado.'), 'erro');
      } finally {
        setBuscandoManual(false);
      }
      return;
    }

    avisar('Ocorrência não encontrada na lista. Insira o protocolo exato ou o UUID.', 'info');
  };

  const carregarSugestoesConexao = async (ocorrenciaId: string) => {
    setCarregandoSugestoes(true);
    try {
      const res = await inqueritosService.buscarConexoes(ocorrenciaId);
      setSugestoes(res);
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    } finally {
      setCarregandoSugestoes(false);
    }
  };

  const selecionarInquerito = async (inq: Inquerito) => {
    setSelecionado(inq);
    setSugestoes([]);
    // Se o inquérito tem ocorrências, busca sugestões da primeira
    if (inq.ocorrencias.length > 0) {
      carregarSugestoesConexao(inq.ocorrencias[0].id);
    }
  };

  const executarVinculacao = async (ocorrenciaId: string) => {
    if (!selecionado) return;
    try {
      const atualizado = await inqueritosService.vincularOcorrencias(selecionado.id, [ocorrenciaId]);
      setSelecionado(atualizado);
      avisar(t('inqueritos:notificacoes.vinculado_sucesso'), 'sucesso');
      carregarInqueritos();
      carregarSugestoesConexao(ocorrenciaId);
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    }
  };

  const vincularManual = async () => {
    const termo = inputManualVincularId.trim();
    if (!termo || !selecionado) return;

    const encontrada = ocorrenciasValidadas.find(
      (oc) =>
        oc.ocorrencia_id.toLowerCase() === termo.toLowerCase() ||
        oc.numero_protocolo.toLowerCase() === termo.toLowerCase(),
    );

    if (encontrada) {
      await executarVinculacao(encontrada.ocorrencia_id);
      setInputManualVincularId('');
      setModalVincularAberto(false);
      return;
    }

    const isUuid = /^[0-9a-fA-F-]{32,36}$/.test(termo);
    if (isUuid) {
      setBuscandoManualVincular(true);
      try {
        await executarVinculacao(termo);
        setInputManualVincularId('');
        setModalVincularAberto(false);
      } catch (err) {
        avisar(mensagemDeErro(err, 'Erro ao vincular ocorrência pelo ID informado.'), 'erro');
      } finally {
        setBuscandoManualVincular(false);
      }
      return;
    }

    avisar('Informe um protocolo válido ou UUID correspondente.', 'info');
  };

  const executarConclusao = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selecionado) return;
    if (relatorioFinal.trim().length < 10) {
      avisar(t('inqueritos:validacoes.relatorio_min'), 'erro');
      return;
    }
    try {
      const atualizado = await inqueritosService.concluir(selecionado.id, relatorioFinal.trim());
      setSelecionado(atualizado);
      setModalConcluirAberto(false);
      avisar(t('inqueritos:notificacoes.concluido_sucesso'), 'sucesso');
      carregarInqueritos();
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    }
  };

  const renderBadgeStatus = (status: string) => {
    const texto = t(`inqueritos:status.${status}`, { defaultValue: status });
    return <span className={`badge badge-${status}`}>{texto}</span>;
  };

  // Filtragem e paginação para o modal de instauração
  const ocorrenciasFiltradasInstaurar = useMemo(() => {
    if (!buscaInstaurar.trim()) return ocorrenciasValidadas;
    const termo = buscaInstaurar.toLowerCase();
    return ocorrenciasValidadas.filter(
      (oc) =>
        oc.numero_protocolo.toLowerCase().includes(termo) ||
        oc.natureza.toLowerCase().includes(termo) ||
        oc.localizacao.toLowerCase().includes(termo),
    );
  }, [ocorrenciasValidadas, buscaInstaurar]);

  const totalPaginasInstaurar = Math.ceil(ocorrenciasFiltradasInstaurar.length / ITENS_POR_PAGINA) || 1;
  const paginaInstaurarSegura = Math.min(paginaInstaurar, totalPaginasInstaurar);
  const ocorrenciasPaginaInstaurar = useMemo(() => {
    const inicio = (paginaInstaurarSegura - 1) * ITENS_POR_PAGINA;
    return ocorrenciasFiltradasInstaurar.slice(inicio, inicio + ITENS_POR_PAGINA);
  }, [ocorrenciasFiltradasInstaurar, paginaInstaurarSegura]);

  // Filtragem e paginação para o modal de vinculação
  const ocorrenciasFiltradasVincular = useMemo(() => {
    // Exclui ocorrências que já pertencem ao inquérito selecionado
    const idsJaVinculadas = new Set(selecionado?.ocorrencias.map((o) => o.id) || []);
    const disponiveis = ocorrenciasValidadas.filter((o) => !idsJaVinculadas.has(o.ocorrencia_id));

    if (!buscaVincular.trim()) return disponiveis;
    const termo = buscaVincular.toLowerCase();
    return disponiveis.filter(
      (oc) =>
        oc.numero_protocolo.toLowerCase().includes(termo) ||
        oc.natureza.toLowerCase().includes(termo) ||
        oc.localizacao.toLowerCase().includes(termo),
    );
  }, [ocorrenciasValidadas, selecionado, buscaVincular]);

  const totalPaginasVincular = Math.ceil(ocorrenciasFiltradasVincular.length / ITENS_POR_PAGINA) || 1;
  const paginaVincularSegura = Math.min(paginaVincular, totalPaginasVincular);
  const ocorrenciasPaginaVincular = useMemo(() => {
    const inicio = (paginaVincularSegura - 1) * ITENS_POR_PAGINA;
    return ocorrenciasFiltradasVincular.slice(inicio, inicio + ITENS_POR_PAGINA);
  }, [ocorrenciasFiltradasVincular, paginaVincularSegura]);

  return (
    <div className="inqueritos-page" style={{ padding: '1.5rem', maxWidth: '1400px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '1.75rem', fontWeight: 700, color: 'var(--ink)' }}>{t('inqueritos:titulo')}</h1>
          <p style={{ margin: '0.25rem 0 0', color: 'var(--muted)' }}>
            {t('inqueritos:subtitulo')}
          </p>
        </div>
        {tem('DELEGADO') && (
          <button
            className="btn btn-primary"
            onClick={abrirModalInstaurar}
            style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', height: '42px', padding: '0 1.25rem', fontWeight: 600 }}
          >
            <span>+</span> {t('inqueritos:btn_instaurar')}
          </button>
        )}
      </div>

      {/* Filtros por status com GlideSelect */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', gap: '1rem', flexWrap: 'wrap' }}>
        <div style={{ width: '280px' }}>
          <GlideSelect
            value={filtroStatus}
            options={opcoesStatusInquerito}
            onChange={(val) => setFiltroStatus(val)}
            fullWidth
          />
        </div>
        <span style={{ color: 'var(--muted)', fontSize: '0.9rem', fontWeight: 500 }}>
          {t('inqueritos:total')}: <strong>{total}</strong>
        </span>
      </div>

      {/* Grid Principal */}
      <div style={{ display: 'grid', gridTemplateColumns: selecionado ? '1fr 1fr' : '1fr', gap: '1.5rem' }}>
        {/* Lista de Inquéritos */}
        <div style={{ background: 'var(--card)', borderRadius: '8px', border: '1px solid var(--line)', padding: '1rem' }}>
          {carregando ? (
            <p style={{ textAlign: 'center', padding: '2rem', color: 'var(--muted)' }}>{t('inqueritos:carregando')}</p>
          ) : inqueritos.length === 0 ? (
            <p style={{ textAlign: 'center', padding: '2rem', color: 'var(--muted)' }}>{t('inqueritos:nenhum_encontrado')}</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {inqueritos.map((inq) => (
                <div
                  key={inq.id}
                  onClick={() => selecionarInquerito(inq)}
                  style={{
                    padding: '1rem',
                    borderRadius: '8px',
                    border: selecionado?.id === inq.id ? '2px solid var(--primary)' : '1px solid var(--line)',
                    background: selecionado?.id === inq.id ? 'var(--card-hover)' : 'var(--card)',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                    <span style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--primary)' }}>{inq.numero}</span>
                    {renderBadgeStatus(inq.status)}
                  </div>
                  <p style={{ margin: '0 0 0.5rem', fontSize: '0.95rem', color: 'var(--ink)' }}>
                    {inq.ementa.length > 120 ? `${inq.ementa.substring(0, 120)}...` : inq.ementa}
                  </p>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--muted)' }}>
                    <span>{t('inqueritos:tabela.data_abertura')}: {new Date(inq.data_abertura).toLocaleDateString()}</span>
                    <span>{inq.ocorrencias.length} {t('inqueritos:ocorrencias_vinculadas_qtd')}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Detalhes do Inquérito Selecionado */}
        {selecionado && (
          <div style={{ background: 'var(--card)', borderRadius: '8px', border: '1px solid var(--line)', padding: '1.25rem', position: 'sticky', top: '5rem', maxHeight: 'calc(100vh - 6rem)', overflowY: 'auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '1px solid var(--line)', paddingBottom: '0.75rem', marginBottom: '1rem' }}>
              <div>
                <h2 style={{ margin: 0, fontSize: '1.3rem', color: 'var(--primary)' }}>{selecionado.numero}</h2>
                <span style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>
                  {t('inqueritos:detalhes.data_abertura')}: {new Date(selecionado.data_abertura).toLocaleString()}
                </span>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                {renderBadgeStatus(selecionado.status)}
                <button
                  onClick={() => setSelecionado(null)}
                  style={{ border: 'none', background: 'transparent', cursor: 'pointer', fontSize: '1.2rem', color: 'var(--muted)' }}
                  aria-label={t('inqueritos:acoes.fechar')}
                >
                  &times;
                </button>
              </div>
            </div>

            <div style={{ marginBottom: '1rem' }}>
              <h4 style={{ margin: '0 0 0.25rem', fontSize: '0.9rem', color: 'var(--muted)', textTransform: 'uppercase' }}>
                {t('inqueritos:detalhes.descricao_linhas')}
              </h4>
              <p style={{ margin: 0, fontSize: '0.95rem', lineHeight: 1.5, background: 'var(--card-hover)', padding: '0.75rem', borderRadius: '6px', color: 'var(--ink)' }}>
                {selecionado.ementa}
              </p>
            </div>

            {selecionado.relatorio_final && (
              <div style={{ marginBottom: '1rem' }}>
                <h4 style={{ margin: '0 0 0.25rem', fontSize: '0.9rem', color: 'var(--ok)', textTransform: 'uppercase' }}>
                  {t('inqueritos:detalhes.relatorio_final')}
                </h4>
                <p style={{ margin: 0, fontSize: '0.95rem', lineHeight: 1.5, background: 'var(--card-hover)', borderLeft: '3px solid var(--ok)', padding: '0.75rem', borderRadius: '6px', color: 'var(--ink)' }}>
                  {selecionado.relatorio_final}
                </p>
              </div>
            )}

            {/* Ocorrências Vinculadas */}
            <div style={{ marginBottom: '1.25rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 600, color: 'var(--ink)' }}>
                  {t('inqueritos:detalhes.ocorrencias_vinculadas')} ({selecionado.ocorrencias.length})
                </h3>
                {selecionado.status === 'EM_ANDAMENTO' && tem('DELEGADO') && (
                  <button
                    className="btn btn-sm btn-outline"
                    onClick={abrirModalVincular}
                    style={{ fontSize: '0.8rem', padding: '0.25rem 0.65rem', height: '32px' }}
                  >
                    + {t('inqueritos:acoes.vincular')}
                  </button>
                )}
              </div>

              {selecionado.ocorrencias.length === 0 ? (
                <p style={{ fontSize: '0.9rem', color: 'var(--muted)', fontStyle: 'italic' }}>
                  {t('inqueritos:nenhuma_ocorrencia')}
                </p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {selecionado.ocorrencias.map((oc, index) => (
                    <div
                      key={oc.id}
                      style={{
                        padding: '0.65rem 0.85rem',
                        border: index === 0 ? '1px solid var(--primary)' : '1px solid var(--line)',
                        borderRadius: '6px',
                        background: index === 0 ? 'var(--card-hover)' : 'var(--card)',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                      }}
                    >
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                          <span style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--ink)' }}>{oc.numero_protocolo}</span>
                          {index === 0 ? (
                            <span
                              style={{
                                fontSize: '0.72rem',
                                fontWeight: 700,
                                padding: '0.15rem 0.45rem',
                                borderRadius: '4px',
                                background: 'rgba(234, 179, 8, 0.2)',
                                color: 'var(--warn, #eab308)',
                                border: '1px solid rgba(234, 179, 8, 0.4)',
                              }}
                            >
                              ⭐ {t('inqueritos:fato_principal')}
                            </span>
                          ) : (
                            <span
                              style={{
                                fontSize: '0.72rem',
                                fontWeight: 500,
                                padding: '0.15rem 0.45rem',
                                borderRadius: '4px',
                                background: 'var(--bg)',
                                color: 'var(--muted)',
                                border: '1px solid var(--line)',
                              }}
                            >
                              {t('inqueritos:vinculada')}
                            </span>
                          )}
                          <span style={{ fontSize: '0.85rem', color: 'var(--ink)' }}>{oc.natureza}</span>
                        </div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--muted)', marginTop: '0.2rem' }}>
                          {oc.localizacao} &bull; {new Date(oc.data_hora_fato).toLocaleString()}
                        </div>
                      </div>
                      <button
                        className="btn btn-sm btn-ghost"
                        onClick={() => carregarSugestoesConexao(oc.id)}
                        title={t('inqueritos:acoes.buscar_conexoes')}
                        style={{ fontSize: '0.75rem' }}
                      >
                        🔍 {t('inqueritos:acoes.buscar_conexoes')}
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Painel do Motor de Conexões Inteligentes */}
            {selecionado.status === 'EM_ANDAMENTO' && (
              <div style={{ marginBottom: '1.25rem', border: '1px solid var(--primary-glow, var(--line))', borderRadius: '8px', padding: '0.85rem', background: 'var(--card-hover)' }}>
                <h4 style={{ margin: '0 0 0.5rem', color: 'var(--primary)', fontSize: '0.95rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <span>⚡</span> {t('inqueritos:modal_conexoes.titulo')}
                </h4>
                {carregandoSugestoes ? (
                  <p style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>{t('inqueritos:modal_conexoes.subtitulo')}</p>
                ) : sugestoes.length === 0 ? (
                  <p style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>{t('inqueritos:modal_conexoes.nenhuma_sugestao')}</p>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {sugestoes.map((sug) => (
                      <div
                        key={sug.ocorrencia_id}
                        style={{
                          background: 'var(--card)',
                          padding: '0.65rem 0.75rem',
                          borderRadius: '6px',
                          border: '1px solid var(--line)',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                        }}
                      >
                        <div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <span style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--ink)' }}>{sug.numero_protocolo}</span>
                            <span
                              style={{
                                fontSize: '0.75rem',
                                padding: '0.1rem 0.4rem',
                                borderRadius: '10px',
                                background: sug.score_similaridade >= 100 ? 'rgba(239, 68, 68, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                                color: sug.score_similaridade >= 100 ? 'var(--danger)' : 'var(--warn)',
                                fontWeight: 700,
                              }}
                            >
                              {t('inqueritos:modal_conexoes.score')}: {sug.score_similaridade}
                            </span>
                          </div>
                          <div style={{ fontSize: '0.8rem', color: 'var(--ink)' }}>{sug.natureza}</div>
                          <div style={{ fontSize: '0.75rem', color: 'var(--muted)' }}>
                            {t('inqueritos:modal_conexoes.motivos')}: {sug.motivos.join('; ')}
                          </div>
                        </div>
                        {tem('DELEGADO') && (
                          <button
                            className="btn btn-sm btn-primary"
                            onClick={() => executarVinculacao(sug.ocorrencia_id)}
                            style={{ fontSize: '0.75rem', padding: '0.25rem 0.6rem', height: '32px' }}
                          >
                            + {t('inqueritos:acoes.vincular')}
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Ações de Conclusão */}
            {selecionado.status === 'EM_ANDAMENTO' && tem('DELEGADO') && (
              <div style={{ borderTop: '1px solid var(--line)', paddingTop: '1rem', display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
                <button
                  className="btn btn-primary"
                  onClick={() => {
                    setRelatorioFinal('');
                    setModalConcluirAberto(true);
                  }}
                  style={{ fontWeight: 600, height: '42px', padding: '0 1.25rem' }}
                >
                  {t('inqueritos:modal_concluir.btn_submit')}
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Modal de Instauração com Seleção Paginada e Ocorrência Principal */}
      {modalInstaurarAberto && (
        <div className="modal-backdrop" style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.65)', backdropFilter: 'blur(4px)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1200 }}>
          <div style={{ background: 'var(--card)', color: 'var(--ink)', padding: '1.75rem', borderRadius: '12px', border: '1px solid var(--line)', maxWidth: '720px', width: '92%', maxHeight: '90vh', overflowY: 'auto', boxShadow: 'var(--shadow-pop)' }}>
            <h2 style={{ marginTop: 0, marginBottom: '1rem', color: 'var(--ink)', fontSize: '1.35rem' }}>{t('inqueritos:modal_instaurar.titulo')}</h2>
            <form onSubmit={executarInstauracao}>
              <div style={{ marginBottom: '1.25rem' }}>
                <label style={{ display: 'block', fontWeight: 600, marginBottom: '0.35rem', color: 'var(--ink)', fontSize: '0.9rem' }}>
                  {t('inqueritos:modal_instaurar.campo_descricao')}
                </label>
                <textarea
                  className="form-control"
                  rows={3}
                  value={ementa}
                  onChange={(e) => setEmenta(e.target.value)}
                  placeholder={t('inqueritos:modal_instaurar.placeholder_descricao')}
                  style={{ width: '100%', padding: '0.75rem', background: 'var(--bg)', color: 'var(--ink)', border: '1px solid var(--line)', borderRadius: '8px' }}
                  required
                />
              </div>

              {/* Seção de Ocorrências Elegíveis */}
              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', fontWeight: 600, marginBottom: '0.35rem', color: 'var(--ink)', fontSize: '0.9rem' }}>
                  {t('inqueritos:modal_vincular.titulo')}
                </label>

                {/* Barra de Filtro e Inclusão Manual */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: '0.5rem', marginBottom: '0.75rem' }}>
                  <input
                    type="text"
                    value={buscaInstaurar}
                    onChange={(e) => {
                      setBuscaInstaurar(e.target.value);
                      setPaginaInstaurar(1);
                    }}
                    placeholder={t('inqueritos:busca_placeholder')}
                    style={{
                      height: '42px',
                      padding: '0.6rem 0.8rem',
                      background: 'var(--bg)',
                      color: 'var(--ink)',
                      border: '1px solid var(--line)',
                      borderRadius: '8px',
                    }}
                  />
                  <input
                    type="text"
                    value={inputManualId}
                    onChange={(e) => setInputManualId(e.target.value)}
                    placeholder={t('inqueritos:adicionar_manual_placeholder')}
                    style={{
                      height: '42px',
                      padding: '0.6rem 0.8rem',
                      background: 'var(--bg)',
                      color: 'var(--ink)',
                      border: '1px solid var(--line)',
                      borderRadius: '8px',
                    }}
                  />
                  <button
                    type="button"
                    className="btn btn-outline"
                    onClick={adicionarOcorrenciaManual}
                    disabled={!inputManualId.trim() || buscandoManual}
                    style={{ height: '42px', padding: '0 1rem', display: 'flex', alignItems: 'center', gap: '0.35rem', whiteSpace: 'nowrap' }}
                  >
                    {buscandoManual ? '...' : `+ ${t('inqueritos:btn_adicionar_id')}`}
                  </button>
                </div>

                {/* Lista Paginada */}
                {ocorrenciasFiltradasInstaurar.length === 0 ? (
                  <p style={{ fontSize: '0.85rem', color: 'var(--muted)', padding: '1rem', textAlign: 'center', border: '1px solid var(--line)', borderRadius: '8px' }}>
                    {ocorrenciasValidadas.length === 0 ? t('inqueritos:modal_vincular.nenhuma_elegivel') : t('inqueritos:nenhum_resultado_busca')}
                  </p>
                ) : (
                  <div style={{ border: '1px solid var(--line)', borderRadius: '8px', padding: '0.6rem', background: 'var(--bg)' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', maxHeight: '280px', overflowY: 'auto' }}>
                      {ocorrenciasPaginaInstaurar.map((oc) => {
                        const isSelected = ocorrenciasSelecionadasIds.includes(oc.ocorrencia_id);
                        const isPrincipal = ocorrenciaPrincipalId === oc.ocorrencia_id;
                        return (
                          <div
                            key={oc.ocorrencia_id}
                            style={{
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'space-between',
                              padding: '0.6rem 0.75rem',
                              borderRadius: '8px',
                              border: isSelected ? '1px solid var(--primary)' : '1px solid var(--line)',
                              background: isSelected ? 'var(--card-hover)' : 'var(--card)',
                              transition: 'all 0.15s ease',
                            }}
                          >
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flex: 1, minWidth: 0 }}>
                              <SpringCheck
                                checked={isSelected}
                                strike="none"
                                onChange={(checked) => {
                                  if (checked) {
                                    setOcorrenciasSelecionadasIds((prev) => [...prev, oc.ocorrencia_id]);
                                    if (!ocorrenciaPrincipalId) {
                                      setOcorrenciaPrincipalId(oc.ocorrencia_id);
                                    }
                                  } else {
                                    setOcorrenciasSelecionadasIds((prev) => {
                                      const rest = prev.filter((id) => id !== oc.ocorrencia_id);
                                      if (ocorrenciaPrincipalId === oc.ocorrencia_id) {
                                        setOcorrenciaPrincipalId(rest[0] || null);
                                      }
                                      return rest;
                                    });
                                  }
                                }}
                              />
                              <div style={{ minWidth: 0, overflow: 'hidden' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                                  <span style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--ink)' }}>{oc.numero_protocolo}</span>
                                  <span style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>•</span>
                                  <span style={{ fontSize: '0.85rem', color: 'var(--ink)' }}>{oc.natureza}</span>
                                </div>
                                <div style={{ fontSize: '0.75rem', color: 'var(--muted)', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                                  {oc.localizacao} • {new Date(oc.data_hora_fato).toLocaleDateString()}
                                </div>
                              </div>
                            </div>

                            {isSelected && (
                              <div style={{ marginLeft: '0.5rem', flexShrink: 0 }}>
                                {isPrincipal ? (
                                  <span
                                    style={{
                                      display: 'inline-flex',
                                      alignItems: 'center',
                                      gap: '0.25rem',
                                      fontSize: '0.75rem',
                                      fontWeight: 700,
                                      padding: '0.2rem 0.5rem',
                                      borderRadius: '6px',
                                      background: 'rgba(234, 179, 8, 0.2)',
                                      color: 'var(--warn, #eab308)',
                                      border: '1px solid rgba(234, 179, 8, 0.4)',
                                    }}
                                  >
                                    ⭐ {t('inqueritos:fato_principal')}
                                  </span>
                                ) : (
                                  <button
                                    type="button"
                                    className="btn btn-sm btn-ghost"
                                    onClick={() => setOcorrenciaPrincipalId(oc.ocorrencia_id)}
                                    style={{ fontSize: '0.75rem', padding: '0.2rem 0.5rem', color: 'var(--muted)' }}
                                    title={t('inqueritos:tornar_principal')}
                                  >
                                    ☆ {t('inqueritos:tornar_principal')}
                                  </button>
                                )}
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>

                    {/* Paginação com Botões de Seta Simples */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.75rem', paddingTop: '0.5rem', borderTop: '1px solid var(--line)' }}>
                      <span style={{ fontSize: '0.82rem', color: 'var(--muted)' }}>
                        {t('inqueritos:paginacao.pagina')} {paginaInstaurarSegura} {t('inqueritos:paginacao.de')} {totalPaginasInstaurar} ({ocorrenciasFiltradasInstaurar.length} {t('inqueritos:paginacao.registros')})
                      </span>
                      <div style={{ display: 'flex', gap: '0.4rem' }}>
                        <button
                          type="button"
                          className="btn btn-sm btn-outline"
                          onClick={() => setPaginaInstaurar((p) => Math.max(1, p - 1))}
                          disabled={paginaInstaurarSegura <= 1}
                          style={{ minWidth: '36px', height: '32px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold' }}
                          title="Página anterior"
                        >
                          &lt;
                        </button>
                        <button
                          type="button"
                          className="btn btn-sm btn-outline"
                          onClick={() => setPaginaInstaurar((p) => Math.min(totalPaginasInstaurar, p + 1))}
                          disabled={paginaInstaurarSegura >= totalPaginasInstaurar}
                          style={{ minWidth: '36px', height: '32px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold' }}
                          title="Próxima página"
                        >
                          &gt;
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                {/* Resumo de Ocorrências Selecionadas */}
                {ocorrenciasSelecionadasIds.length > 0 && (
                  <div style={{ marginTop: '0.75rem', padding: '0.6rem 0.8rem', background: 'var(--card)', borderRadius: '8px', border: '1px dashed var(--line)' }}>
                    <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--muted)', marginBottom: '0.4rem' }}>
                      {t('inqueritos:ocorrencias_selecionadas')} ({ocorrenciasSelecionadasIds.length}):
                    </div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                      {ocorrenciasSelecionadasIds.map((id) => {
                        const item = ocorrenciasValidadas.find((o) => o.ocorrencia_id === id);
                        const isPrinc = ocorrenciaPrincipalId === id;
                        return (
                          <span
                            key={id}
                            style={{
                              fontSize: '0.75rem',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '0.35rem',
                              padding: '0.2rem 0.5rem',
                              borderRadius: '6px',
                              background: isPrinc ? 'rgba(37, 99, 235, 0.15)' : 'var(--bg)',
                              color: isPrinc ? 'var(--primary)' : 'var(--ink)',
                              border: isPrinc ? '1px solid var(--primary)' : '1px solid var(--line)',
                            }}
                          >
                            {isPrinc && '⭐'} {item?.numero_protocolo || id.slice(0, 8)}
                            <button
                              type="button"
                              onClick={() => {
                                setOcorrenciasSelecionadasIds((prev) => {
                                  const rest = prev.filter((i) => i !== id);
                                  if (ocorrenciaPrincipalId === id) setOcorrenciaPrincipalId(rest[0] || null);
                                  return rest;
                                });
                              }}
                              style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--muted)', padding: 0, fontSize: '0.85rem' }}
                            >
                              &times;
                            </button>
                          </span>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
                <button type="button" className="btn btn-ghost" onClick={() => setModalInstaurarAberto(false)} style={{ height: '42px' }}>
                  {t('inqueritos:acoes.cancelar')}
                </button>
                <button type="submit" className="btn btn-primary" style={{ height: '42px', padding: '0 1.5rem', fontWeight: 600 }}>
                  {t('inqueritos:modal_instaurar.btn_submit')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal de Conclusão */}
      {modalConcluirAberto && (
        <div className="modal-backdrop" style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.65)', backdropFilter: 'blur(4px)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1200 }}>
          <div style={{ background: 'var(--card)', color: 'var(--ink)', padding: '1.75rem', borderRadius: '12px', border: '1px solid var(--line)', maxWidth: '600px', width: '90%', boxShadow: 'var(--shadow-pop)' }}>
            <h2 style={{ marginTop: 0, color: 'var(--ink)', fontSize: '1.35rem' }}>{t('inqueritos:modal_concluir.titulo')} ({selecionado?.numero})</h2>
            <form onSubmit={executarConclusao}>
              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', fontWeight: 600, marginBottom: '0.35rem', color: 'var(--ink)', fontSize: '0.9rem' }}>
                  {t('inqueritos:modal_concluir.campo_relatorio')}
                </label>
                <textarea
                  className="form-control"
                  rows={6}
                  value={relatorioFinal}
                  onChange={(e) => setRelatorioFinal(e.target.value)}
                  placeholder={t('inqueritos:modal_concluir.placeholder_relatorio')}
                  style={{ width: '100%', padding: '0.75rem', background: 'var(--bg)', color: 'var(--ink)', border: '1px solid var(--line)', borderRadius: '8px' }}
                  required
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
                <button type="button" className="btn btn-ghost" onClick={() => setModalConcluirAberto(false)} style={{ height: '42px' }}>
                  {t('inqueritos:acoes.cancelar')}
                </button>
                <button type="submit" className="btn btn-primary" style={{ height: '42px', padding: '0 1.5rem', fontWeight: 600 }}>
                  {t('inqueritos:modal_concluir.btn_submit')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal Vincular Ocorrência Avulsa com Paginação e Busca */}
      {modalVincularAberto && (
        <div className="modal-backdrop" style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.65)', backdropFilter: 'blur(4px)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1200 }}>
          <div style={{ background: 'var(--card)', color: 'var(--ink)', padding: '1.75rem', borderRadius: '12px', border: '1px solid var(--line)', maxWidth: '680px', width: '92%', maxHeight: '90vh', overflowY: 'auto', boxShadow: 'var(--shadow-pop)' }}>
            <h2 style={{ marginTop: 0, marginBottom: '0.25rem', color: 'var(--ink)', fontSize: '1.35rem' }}>{t('inqueritos:modal_vincular.titulo')}</h2>
            <p style={{ color: 'var(--muted)', fontSize: '0.9rem', marginBottom: '1.25rem' }}>{t('inqueritos:modal_vincular.subtitulo')}</p>

            {/* Busca e Inclusão Manual */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: '0.5rem', marginBottom: '0.75rem' }}>
              <input
                type="text"
                value={buscaVincular}
                onChange={(e) => {
                  setBuscaVincular(e.target.value);
                  setPaginaVincular(1);
                }}
                placeholder={t('inqueritos:busca_placeholder')}
                style={{
                  height: '42px',
                  padding: '0.6rem 0.8rem',
                  background: 'var(--bg)',
                  color: 'var(--ink)',
                  border: '1px solid var(--line)',
                  borderRadius: '8px',
                }}
              />
              <input
                type="text"
                value={inputManualVincularId}
                onChange={(e) => setInputManualVincularId(e.target.value)}
                placeholder={t('inqueritos:adicionar_manual_placeholder')}
                style={{
                  height: '42px',
                  padding: '0.6rem 0.8rem',
                  background: 'var(--bg)',
                  color: 'var(--ink)',
                  border: '1px solid var(--line)',
                  borderRadius: '8px',
                }}
              />
              <button
                type="button"
                className="btn btn-outline"
                onClick={vincularManual}
                disabled={!inputManualVincularId.trim() || buscandoManualVincular}
                style={{ height: '42px', padding: '0 1rem', display: 'flex', alignItems: 'center', gap: '0.35rem', whiteSpace: 'nowrap' }}
              >
                {buscandoManualVincular ? '...' : `+ ${t('inqueritos:acoes.vincular')}`}
              </button>
            </div>

            {ocorrenciasFiltradasVincular.length === 0 ? (
              <p style={{ fontSize: '0.85rem', color: 'var(--muted)', padding: '1.5rem', textAlign: 'center', border: '1px solid var(--line)', borderRadius: '8px' }}>
                {ocorrenciasValidadas.length === 0 ? t('inqueritos:modal_vincular.nenhuma_elegivel') : t('inqueritos:nenhum_resultado_busca')}
              </p>
            ) : (
              <div style={{ border: '1px solid var(--line)', borderRadius: '8px', padding: '0.6rem', background: 'var(--bg)', marginBottom: '1.25rem' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', maxHeight: '280px', overflowY: 'auto' }}>
                  {ocorrenciasPaginaVincular.map((oc) => (
                    <div
                      key={oc.ocorrencia_id}
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        padding: '0.6rem 0.75rem',
                        border: '1px solid var(--line)',
                        borderRadius: '8px',
                        background: 'var(--card)',
                      }}
                    >
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <span style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--ink)' }}>{oc.numero_protocolo}</span>
                          <span style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>•</span>
                          <span style={{ fontSize: '0.85rem', color: 'var(--ink)' }}>{oc.natureza}</span>
                        </div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--muted)', marginTop: '0.2rem' }}>
                          {oc.localizacao} • {new Date(oc.data_hora_fato).toLocaleDateString()}
                        </div>
                      </div>
                      <button
                        className="btn btn-sm btn-primary"
                        onClick={async () => {
                          await executarVinculacao(oc.ocorrencia_id);
                          setModalVincularAberto(false);
                        }}
                        style={{ height: '32px', padding: '0 0.8rem', fontSize: '0.8rem' }}
                      >
                        + {t('inqueritos:acoes.vincular')}
                      </button>
                    </div>
                  ))}
                </div>

                {/* Paginação */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.75rem', paddingTop: '0.5rem', borderTop: '1px solid var(--line)' }}>
                  <span style={{ fontSize: '0.82rem', color: 'var(--muted)' }}>
                    {t('inqueritos:paginacao.pagina')} {paginaVincularSegura} {t('inqueritos:paginacao.de')} {totalPaginasVincular} ({ocorrenciasFiltradasVincular.length} {t('inqueritos:paginacao.registros')})
                  </span>
                  <div style={{ display: 'flex', gap: '0.4rem' }}>
                    <button
                      type="button"
                      className="btn btn-sm btn-outline"
                      onClick={() => setPaginaVincular((p) => Math.max(1, p - 1))}
                      disabled={paginaVincularSegura <= 1}
                      style={{ minWidth: '36px', height: '32px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold' }}
                      title="Página anterior"
                    >
                      &lt;
                    </button>
                    <button
                      type="button"
                      className="btn btn-sm btn-outline"
                      onClick={() => setPaginaVincular((p) => Math.min(totalPaginasVincular, p + 1))}
                      disabled={paginaVincularSegura >= totalPaginasVincular}
                      style={{ minWidth: '36px', height: '32px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold' }}
                      title="Próxima página"
                    >
                      &gt;
                    </button>
                  </div>
                </div>
              </div>
            )}

            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button type="button" className="btn btn-ghost" onClick={() => setModalVincularAberto(false)} style={{ height: '42px' }}>
                {t('inqueritos:acoes.fechar')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default InqueritosPage;
