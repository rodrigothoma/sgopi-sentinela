import { API_BASE_URL } from './api';
import { sessao } from './sessao';
import type { EventoTempoReal } from '../types/api';

export type EstadoConexao = 'conectando' | 'conectado' | 'reconectando' | 'desconectado';

const BACKOFF_MS = [1000, 2000, 4000, 8000, 16000, 30000]; // RNF04*: 1/2/4/8 s, máx. 30 s

/**
 * Cliente WebSocket de /v1/tempo-real (RF02 / RNF01) com reconexão exponencial.
 * Ao (re)conectar, o consumidor deve recarregar a carga inicial por REST (callback onReconectar).
 */
export class ClienteTempoReal {
  private ws: WebSocket | null = null;
  private tentativa = 0;
  private timer: number | null = null;
  private keepAlive: number | null = null;
  private ativo = false;

  constructor(
    private readonly onEvento: (e: EventoTempoReal) => void,
    private readonly onEstado: (s: EstadoConexao) => void,
    private readonly onReconectar: () => void,
  ) {}

  conectar(): void {
    this.ativo = true;
    this.abrir();
  }

  fechar(): void {
    this.ativo = false;
    if (this.timer) window.clearTimeout(this.timer);
    if (this.keepAlive) window.clearInterval(this.keepAlive);
    this.ws?.close();
    this.ws = null;
    this.onEstado('desconectado');
  }

  private url(): string {
    // Sem base absoluta, deriva do origin da página (o proxy do Vite repassa o WS).
    const base = API_BASE_URL
      ? API_BASE_URL.replace(/^http/, 'ws')
      : `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}`;
    return `${base}/v1/tempo-real?token=${encodeURIComponent(sessao.token() ?? '')}`;
  }

  private abrir(): void {
    if (!this.ativo) return;
    this.onEstado(this.tentativa === 0 ? 'conectando' : 'reconectando');
    const ws = new WebSocket(this.url());
    this.ws = ws;
    ws.onopen = () => {
      const reconexao = this.tentativa > 0;
      this.tentativa = 0;
      this.onEstado('conectado');
      if (reconexao) this.onReconectar();
      this.keepAlive = window.setInterval(() => ws.readyState === WebSocket.OPEN && ws.send('ping'), 25000);
    };
    ws.onmessage = (m) => {
      try {
        this.onEvento(JSON.parse(m.data as string) as EventoTempoReal);
      } catch {
        /* mensagem inválida ignorada */
      }
    };
    ws.onclose = (ev) => {
      if (this.keepAlive) window.clearInterval(this.keepAlive);
      if (!this.ativo || ev.code === 1008) {
        this.onEstado('desconectado');
        return;
      }
      const espera = BACKOFF_MS[Math.min(this.tentativa, BACKOFF_MS.length - 1)];
      this.tentativa += 1;
      this.onEstado('reconectando');
      this.timer = window.setTimeout(() => this.abrir(), espera);
    };
    ws.onerror = () => ws.close();
  }
}
