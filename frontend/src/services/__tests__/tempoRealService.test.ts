import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../api', () => ({ API_BASE_URL: '' }));
vi.mock('../sessao', () => ({ sessao: { token: () => 'token-ficticio' } }));

class SocketFake {
  static OPEN = 1;
  static instancias: SocketFake[] = [];
  readyState = SocketFake.OPEN;
  onopen: (() => void) | null = null;
  onclose: ((evento: { code: number }) => void) | null = null;
  onmessage: ((evento: { data: string }) => void) | null = null;
  onerror: (() => void) | null = null;
  send = vi.fn();
  close = vi.fn(() => this.onclose?.({ code: 1000 }));

  constructor() {
    SocketFake.instancias.push(this);
  }
}

beforeEach(() => {
  vi.resetModules();
  vi.useFakeTimers();
  SocketFake.instancias = [];
  vi.stubGlobal('WebSocket', SocketFake);
  vi.stubGlobal('window', {
    location: { protocol: 'http:', host: 'teste.local' },
    setInterval, clearInterval, setTimeout, clearTimeout, dispatchEvent: vi.fn(),
  });
});

afterEach(() => {
  vi.clearAllTimers();
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe('Observer do canal compartilhado', () => {
  it('entrega imediatamente o estado atual para um observador tardio', async () => {
    const { assinarTempoReal } = await import('../tempoRealService');
    const primeiro = vi.fn();
    const tardio = vi.fn();
    const sairA = assinarTempoReal(undefined, undefined, primeiro);
    SocketFake.instancias[0].onopen?.();
    const sairB = assinarTempoReal(undefined, undefined, tardio);
    expect(tardio).toHaveBeenCalledExactlyOnceWith('conectado');
    expect(SocketFake.instancias).toHaveLength(1);
    sairB(); sairA();
  });

  it('notifica conexão inicial uma única vez e compartilha eventos', async () => {
    const { assinarTempoReal } = await import('../tempoRealService');
    const estado = vi.fn();
    const eventoA = vi.fn();
    const eventoB = vi.fn();
    const sairA = assinarTempoReal(eventoA, undefined, estado);
    const sairB = assinarTempoReal(eventoB);
    expect(estado).toHaveBeenCalledExactlyOnceWith('conectando');
    const evento = { tipo: 'PosicaoAtualizada', ocorrido_em: '2026-11-16T12:00:00Z', dados: { viatura_id: 'v1' } };
    SocketFake.instancias[0].onmessage?.({ data: JSON.stringify(evento) });
    expect(eventoA).toHaveBeenCalledExactlyOnceWith(evento);
    expect(eventoB).toHaveBeenCalledExactlyOnceWith(evento);
    sairA();
    expect(SocketFake.instancias[0].close).not.toHaveBeenCalled();
    sairB();
    expect(SocketFake.instancias[0].close).toHaveBeenCalledTimes(1);
  });

  it('entrega o estado de reconexão, mas não repete eventos antigos', async () => {
    const { assinarTempoReal } = await import('../tempoRealService');
    const reconectar = vi.fn();
    const sairA = assinarTempoReal(undefined, reconectar);
    const socket = SocketFake.instancias[0];
    socket.onopen?.();
    socket.onclose?.({ code: 1006 });
    const estado = vi.fn();
    const evento = vi.fn();
    const sairB = assinarTempoReal(evento, undefined, estado);
    expect(estado).toHaveBeenCalledExactlyOnceWith('reconectando');
    expect(evento).not.toHaveBeenCalled();
    vi.advanceTimersByTime(1000);
    SocketFake.instancias[1].onopen?.();
    expect(estado).toHaveBeenLastCalledWith('conectado');
    expect(reconectar).toHaveBeenCalledTimes(1);
    sairB(); sairA();
  });

  it('fecha a última assinatura e inicia novo ciclo sem estado antigo', async () => {
    const { assinarTempoReal } = await import('../tempoRealService');
    const sair = assinarTempoReal();
    SocketFake.instancias[0].onopen?.();
    sair();
    const estado = vi.fn();
    const cancelar = assinarTempoReal(undefined, undefined, estado);
    expect(estado).toHaveBeenCalledExactlyOnceWith('conectando');
    expect(SocketFake.instancias).toHaveLength(2);
    cancelar();
  });
});
