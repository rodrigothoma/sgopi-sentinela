import { describe, expect, it } from 'vitest';
import {
  ESPERA_ATENCAO_HORAS,
  ESPERA_CRITICA_HORAS,
  calcularEspera,
} from '../espera';

const AGORA = Date.parse('2026-11-08T12:00:00Z');
const hAtras = (horas: number): string => new Date(AGORA - horas * 3_600_000).toISOString();

describe('calcularEspera', () => {
  it('não conta espera em status que não aguardam decisão', () => {
    for (const status of ['VALIDADA', 'EM_ATENDIMENTO', 'ENCERRADA', 'ARQUIVADA', 'EXCLUIDA', 'REJEITADA'] as const) {
      expect(calcularEspera(hAtras(99), status, AGORA)).toBeNull();
    }
  });

  it('conta espera enquanto a ocorrência depende de decisão', () => {
    expect(calcularEspera(hAtras(1), 'AGUARDANDO_REVISAO', AGORA)).not.toBeNull();
    expect(calcularEspera(hAtras(1), 'EM_CORRECAO', AGORA)).not.toBeNull();
  });

  it('classifica o nível pelos limiares de atenção e crítico', () => {
    expect(calcularEspera(hAtras(1), 'AGUARDANDO_REVISAO', AGORA)?.nivel).toBe('normal');
    expect(calcularEspera(hAtras(ESPERA_ATENCAO_HORAS), 'AGUARDANDO_REVISAO', AGORA)?.nivel).toBe('atencao');
    expect(calcularEspera(hAtras(10), 'AGUARDANDO_REVISAO', AGORA)?.nivel).toBe('atencao');
    expect(calcularEspera(hAtras(ESPERA_CRITICA_HORAS), 'AGUARDANDO_REVISAO', AGORA)?.nivel).toBe('critico');
    expect(calcularEspera(hAtras(80), 'AGUARDANDO_REVISAO', AGORA)?.nivel).toBe('critico');
  });

  it('formata o tempo decorrido, em dias acima de 24 h', () => {
    expect(calcularEspera(hAtras(2), 'AGUARDANDO_REVISAO', AGORA)?.texto).toBe('2 h');
    expect(calcularEspera(hAtras(52), 'AGUARDANDO_REVISAO', AGORA)?.texto).toBe('2 d 4 h');
  });

  it('trata data inválida como ausência de espera, sem quebrar', () => {
    expect(calcularEspera('nao-e-data', 'AGUARDANDO_REVISAO', AGORA)).toBeNull();
    expect(calcularEspera('', 'AGUARDANDO_REVISAO', AGORA)).toBeNull();
  });

  it('não produz tempo negativo quando a criação está no futuro', () => {
    const futuro = new Date(AGORA + 3_600_000).toISOString();
    expect(calcularEspera(futuro, 'AGUARDANDO_REVISAO', AGORA)?.texto).toBe('0 s');
  });
});
