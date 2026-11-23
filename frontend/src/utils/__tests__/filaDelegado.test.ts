import { describe, expect, it, vi } from 'vitest';
import { inserirOrdenado, resumoDaNotificacao } from '../filaDelegado';

const evento = {
  ocorrencia_id: 'oc-1', numero_protocolo: 'SGOPI-2026-1', natureza: 'Furto',
  localizacao: 'Centro', latitude: -29.78, longitude: -55.79,
  criada_em: '2026-11-09T12:00:00Z', agente_policial_id: 'ag-1',
  origem: 'PUBLICA', prioridade: 'ALTA',
};

describe('fila do Delegado', () => {
  it('ordena por prioridade e depois pela criação, preservando a entrada', () => {
    const media = resumoDaNotificacao({ ...evento, ocorrencia_id: 'media', prioridade: 'MEDIA' });
    const alta = resumoDaNotificacao(evento);
    const antiga = resumoDaNotificacao({ ...evento, ocorrencia_id: 'antiga', criada_em: '2026-11-08T12:00:00Z' });
    const urgente = resumoDaNotificacao({ ...evento, ocorrencia_id: 'urgente', prioridade: 'URGENTE' });
    const itens = [media, alta, antiga];
    expect(inserirOrdenado(itens, urgente).map((o) => o.ocorrencia_id)).toEqual(['urgente', 'antiga', 'oc-1', 'media']);
    expect(itens).toEqual([media, alta, antiga]);
  });

  it('converte o evento mantendo o contrato atual de resumo', () => {
    expect(resumoDaNotificacao(evento)).toEqual({
      ...evento, status: 'AGUARDANDO_REVISAO', data_hora_fato: evento.criada_em,
      atualizada_em: evento.criada_em, versao: 0,
    });
  });

  it('mantém os valores padrão atuais quando o evento não traz campos', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-11-09T12:00:00Z'));
    try {
      expect(resumoDaNotificacao({})).toMatchObject({
        ocorrencia_id: '', latitude: 0, longitude: 0, origem: 'POLICIAL', prioridade: 'MEDIA',
        criada_em: '2026-11-09T12:00:00.000Z', status: 'AGUARDANDO_REVISAO', versao: 0,
      });
    } finally {
      vi.useRealTimers();
    }
  });
});
