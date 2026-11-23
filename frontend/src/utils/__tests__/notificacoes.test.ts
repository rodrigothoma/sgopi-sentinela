import { describe, expect, it, vi } from 'vitest';
import { inserirNotificacao, LIMITE_NOTIFICACOES, notificacaoDoEvento } from '../notificacoes';

describe('dados do sino', () => {
  it('mantém os campos recebidos e inicia a notificação como não lida', () => {
    const dados = {
      id: 'n1', usuario_id: 'u1', titulo: 'Nova ocorrência', mensagem: 'Centro',
      tipo: 'NOVA_OCORRENCIA', prioridade: 'ALTA', criada_em: '2026-11-09T12:00:00Z', link: '/fila?ocorrencia=1',
    };
    expect(notificacaoDoEvento(dados)).toEqual({ ...dados, lida: false });
  });

  it('preserva os valores padrão anteriores para campos ausentes', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-11-09T12:00:00Z'));
    try {
      expect(notificacaoDoEvento({})).toEqual({
        id: '', usuario_id: '', titulo: '', mensagem: '', tipo: 'SISTEMA', prioridade: 'MEDIA',
        lida: false, criada_em: '2026-11-09T12:00:00.000Z', link: null,
      });
    } finally {
      vi.useRealTimers();
    }
  });

  it('coloca a nova no início, limita a lista e não altera a entrada', () => {
    const itens = Array.from({ length: LIMITE_NOTIFICACOES }, (_, id) => notificacaoDoEvento({ id }));
    const nova = notificacaoDoEvento({ id: 'nova' });
    const resultado = inserirNotificacao(itens, nova);
    expect(resultado).toHaveLength(LIMITE_NOTIFICACOES);
    expect(resultado[0]).toEqual(nova);
    expect(resultado[resultado.length - 1].id).toBe('13');
    expect(itens[0].id).toBe('0');
    expect(itens).toHaveLength(LIMITE_NOTIFICACOES);
  });
});
