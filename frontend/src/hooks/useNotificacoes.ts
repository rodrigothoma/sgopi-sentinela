import { useEffect, useRef, useState } from 'react';
import { notificacoesService, type Notificacao } from '../services/notificacoesService';
import { inserirNotificacao, LIMITE_NOTIFICACOES, notificacaoDoEvento } from '../utils/notificacoes';
import { useTempoRealListener } from './useTempoReal';

const INTERVALO_RESUMO_MS = 15000;

interface ControleNotificacoes {
  naoLidas: number;
  notificacoes: Notificacao[];
  carregando: boolean;
  marcarTodasLidas: () => Promise<void>;
  marcarComoLida: (notificacao: Notificacao) => Promise<void>;
}

/** Coordena REST, WebSocket e leitura; a abertura do dropdown continua pertencendo à interface. */
export function useNotificacoes(aberto: boolean): ControleNotificacoes {
  const [naoLidas, setNaoLidas] = useState(0);
  const [notificacoes, setNotificacoes] = useState<Notificacao[]>([]);
  const [carregando, setCarregando] = useState(false);
  const abertoRef = useRef(aberto);
  abertoRef.current = aberto;

  const carregarResumo = async (): Promise<void> => {
    try {
      const res = await notificacoesService.obterResumo();
      setNaoLidas(res.nao_lidas);
    } catch {
      // Uma falha de background mantém o último estado conhecido.
    }
  };

  const carregarLista = async (): Promise<void> => {
    try {
      setCarregando(true);
      const res = await notificacoesService.listar({ limite: LIMITE_NOTIFICACOES });
      setNotificacoes(res.itens);
      setNaoLidas(res.nao_lidas);
    } catch {
      // Preserva a lista atual se a consulta falhar.
    } finally {
      setCarregando(false);
    }
  };

  useTempoRealListener({
    onEvento: (e) => {
      if (e.tipo !== 'NOTIFICACAO_EMITIDA') return;
      const nova = notificacaoDoEvento(e.dados as Record<string, unknown>);
      setNaoLidas((prev) => prev + 1);
      setNotificacoes((prev) => inserirNotificacao(prev, nova));
    },
    onReconectar: () => {
      carregarResumo();
      if (abertoRef.current) carregarLista();
    },
  });

  useEffect(() => {
    carregarResumo();
    const interval = setInterval(carregarResumo, INTERVALO_RESUMO_MS);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (aberto) carregarLista();
  }, [aberto]);

  const marcarTodasLidas = async (): Promise<void> => {
    try {
      await notificacoesService.marcarTodasComoLidas();
      setNaoLidas(0);
      setNotificacoes((prev) => prev.map((n) => ({ ...n, lida: true })));
    } catch (err) {
      console.error('Erro ao marcar todas como lidas:', err);
    }
  };

  const marcarComoLida = async (n: Notificacao): Promise<void> => {
    if (n.lida) return;
    try {
      await notificacoesService.marcarComoLida(n.id);
      setNaoLidas((prev) => Math.max(0, prev - 1));
      setNotificacoes((prev) => prev.map((item) => (item.id === n.id ? { ...item, lida: true } : item)));
    } catch (err) {
      console.error('Erro ao marcar notificação como lida:', err);
    }
  };

  return { naoLidas, notificacoes, carregando, marcarTodasLidas, marcarComoLida };
}
