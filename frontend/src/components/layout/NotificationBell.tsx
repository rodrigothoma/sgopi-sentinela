import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  notificacoesService,
  Notificacao,
  TipoNotificacao,
} from '../../services/notificacoesService';
import './NotificationBell.css';

interface NotificationBellProps {
  colapsada?: boolean;
}

const IconSino = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
    <path d="M13.73 21a2 2 0 0 1-3.46 0" />
  </svg>
);

const IconCheckDuplo = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="18 6 9 17 4 12" />
    <polyline points="22 10 15 17 13 15" />
  </svg>
);

const IconAlerta = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
    <line x1="12" y1="9" x2="12" y2="13" />
    <line x1="12" y1="17" x2="12.01" y2="17" />
  </svg>
);

const IconEscudo = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
  </svg>
);

const IconMensagem = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
  </svg>
);

/** Prancheta com visto: decisão do Delegado sobre a ocorrência do agente (RF04). */
const IconRevisao = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="5" y="4" width="14" height="17" rx="2" />
    <path d="M9 4V3h6v1" />
    <path d="m9 13 2 2 4-4" />
  </svg>
);

const IconInfo = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10" />
    <line x1="12" y1="16" x2="12" y2="12" />
    <line x1="12" y1="8" x2="12.01" y2="8" />
  </svg>
);

export const NotificationBell: React.FC<NotificationBellProps> = ({ colapsada = false }) => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [aberto, setAberto] = useState(false);
  const [naoLidas, setNaoLidas] = useState(0);
  const [notificacoes, setNotificacoes] = useState<Notificacao[]>([]);
  const [carregando, setCarregando] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const carregarResumo = async () => {
    try {
      const res = await notificacoesService.obterResumo();
      setNaoLidas(res.nao_lidas);
    } catch {
      // Falha silenciosa em polling de background
    }
  };

  const carregarLista = async () => {
    try {
      setCarregando(true);
      const res = await notificacoesService.listar({ limite: 15 });
      setNotificacoes(res.itens);
      setNaoLidas(res.nao_lidas);
    } catch {
      // Ignora erro
    } finally {
      setCarregando(false);
    }
  };

  useEffect(() => {
    carregarResumo();
    const interval = setInterval(carregarResumo, 15000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (aberto) {
      carregarLista();
    }
  }, [aberto]);

  // Fechar dropdown ao clicar fora
  useEffect(() => {
    const handleClickFora = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setAberto(false);
      }
    };
    if (aberto) {
      document.addEventListener('mousedown', handleClickFora);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickFora);
    };
  }, [aberto]);

  const handleMarcarTodasLidas = async (e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await notificacoesService.marcarTodasComoLidas();
      setNaoLidas(0);
      setNotificacoes((prev) => prev.map((n) => ({ ...n, lida: true })));
    } catch (err) {
      console.error('Erro ao marcar todas como lidas:', err);
    }
  };

  const handleClicarNotificacao = async (n: Notificacao) => {
    if (!n.lida) {
      try {
        await notificacoesService.marcarComoLida(n.id);
        setNaoLidas((prev) => Math.max(0, prev - 1));
        setNotificacoes((prev) =>
          prev.map((item) => (item.id === n.id ? { ...item, lida: true } : item))
        );
      } catch (err) {
        console.error('Erro ao marcar notificação como lida:', err);
      }
    }

    setAberto(false);

    // Redirecionamento inteligente
    if (n.link) {
      navigate(n.link);
    } else if (n.tipo === 'ALERTA_CRITICIDADE') {
      navigate('/painel');
    } else if (n.tipo === 'ALERTA_VENCIMENTO_MEDIDA') {
      navigate('/medidas');
    } else if (n.tipo === 'COMUNICACAO_INTERAGENCIAS') {
      navigate('/interagencias');
    } else if (n.tipo === 'REVISAO_OCORRENCIA') {
      navigate('/minhas');
    }
  };

  const renderIconeTipo = (tipo: TipoNotificacao) => {
    switch (tipo) {
      case 'ALERTA_CRITICIDADE':
        return <IconAlerta />;
      case 'ALERTA_VENCIMENTO_MEDIDA':
        return <IconEscudo />;
      case 'COMUNICACAO_INTERAGENCIAS':
        return <IconMensagem />;
      case 'REVISAO_OCORRENCIA':
        return <IconRevisao />;
      default:
        return <IconInfo />;
    }
  };

  const formatarDataRelativa = (iso: string) => {
    try {
      const data = new Date(iso);
      const agora = new Date();
      const diffMs = agora.getTime() - data.getTime();
      const diffMin = Math.floor(diffMs / 60000);
      if (diffMin < 1) return t('notificacoes.agora', 'Agora mesmo');
      if (diffMin < 60) return `${diffMin}m`;
      const diffHoras = Math.floor(diffMin / 60);
      if (diffHoras < 24) return `${diffHoras}h`;
      return data.toLocaleDateString();
    } catch {
      return '';
    }
  };

  return (
    <div className={`notification-bell-container ${colapsada ? 'colapsada' : ''}`} ref={containerRef}>
      <button
        type="button"
        className={`notification-bell-btn ${naoLidas > 0 ? 'tem-novas' : ''}`}
        onClick={() => setAberto((prev) => !prev)}
        title={t('notificacoes.titulo', 'Notificações')}
        aria-label={t('notificacoes.titulo', 'Notificações')}
        aria-expanded={aberto}
      >
        <IconSino />
        {naoLidas > 0 && (
          <span className="notification-badge" aria-hidden="true">
            {naoLidas > 99 ? '99+' : naoLidas}
          </span>
        )}
      </button>

      {aberto && (
        <div className="notification-dropdown">
          <div className="notification-dropdown-header">
            <div className="notification-header-title">
              <span>{t('notificacoes.titulo', 'Notificações')}</span>
              {naoLidas > 0 && <span className="notification-counter-badge">{naoLidas}</span>}
            </div>
            {naoLidas > 0 && (
              <button
                type="button"
                className="notification-marcar-todas-btn"
                onClick={handleMarcarTodasLidas}
                title={t('notificacoes.marcar_todas', 'Marcar todas como lidas')}
              >
                <IconCheckDuplo />
                <span>{t('notificacoes.marcar_todas', 'Marcar lidas')}</span>
              </button>
            )}
          </div>

          <div className="notification-dropdown-list">
            {carregando && notificacoes.length === 0 ? (
              <div className="notification-empty">{t('actions.loading', 'Carregando...')}</div>
            ) : notificacoes.length === 0 ? (
              <div className="notification-empty">
                <span className="notification-empty-icon">🔔</span>
                <p>{t('notificacoes.vazio', 'Nenhuma notificação recebida')}</p>
              </div>
            ) : (
              notificacoes.map((item) => (
                <div
                  key={item.id}
                  className={`notification-item ${!item.lida ? 'nao-lida' : ''} prio-${item.prioridade.toLowerCase()}`}
                  onClick={() => handleClicarNotificacao(item)}
                  role="button"
                  tabIndex={0}
                >
                  <div className="notification-item-icon">{renderIconeTipo(item.tipo)}</div>
                  <div className="notification-item-content">
                    <div className="notification-item-top">
                      <span className="notification-item-title">{item.titulo}</span>
                      <span className="notification-item-time">{formatarDataRelativa(item.criada_em)}</span>
                    </div>
                    <p className="notification-item-msg">{item.mensagem}</p>
                  </div>
                  {!item.lida && <span className="notification-unread-dot" />}
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};
