import { describe, expect, it } from 'vitest';
import type { Viatura } from '../../types/api';
import { posicaoDaViatura } from '../inspecaoViatura';

const viatura: Viatura = {
  id: 'v1', prefixo: 'VTR-01', placa: 'ABC1D23', situacao: 'DISPONIVEL',
  latitude: -29.78, longitude: -55.79, posicao_registrada_em: '2026-11-16T12:00:00Z', sinal: 'OK', versao: 1,
};

describe('posição para inspeção da viatura', () => {
  it('mantém latitude e longitude, inclusive quando valem zero', () => {
    expect(posicaoDaViatura(viatura)).toEqual([-29.78, -55.79]);
    expect(posicaoDaViatura({ ...viatura, latitude: 0, longitude: 0 })).toEqual([0, 0]);
  });

  it.each([
    { latitude: null }, { longitude: null }, { latitude: NaN }, { longitude: Infinity },
    { latitude: 91 }, { longitude: -181 },
  ])('não oferece foco para posição incompleta ou inválida: %j', (posicao) => {
    expect(posicaoDaViatura({ ...viatura, ...posicao })).toBeNull();
  });

  it('permite inspecionar a última posição mesmo com sinal desatualizado', () => {
    expect(posicaoDaViatura({ ...viatura, sinal: 'SEM_SINAL' })).toEqual([-29.78, -55.79]);
  });
});
