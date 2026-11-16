import { describe, expect, it } from 'vitest';
import type { OcorrenciaResumo } from '../../types/api';
import {
  MAXIMO_RESULTADOS_BUSCA,
  MAXIMO_TERMOS_BUSCA,
  intersectarResultados,
  mesclarResultadosBusca,
  separarTermos,
  termoBuscavel,
} from '../buscaOcorrencias';

const oc = (id: string, protocolo = `SGOPI-2026-${id}`): OcorrenciaResumo =>
  ({ ocorrencia_id: id, numero_protocolo: protocolo } as OcorrenciaResumo);

describe('termoBuscavel', () => {
  it('exige um mínimo de caracteres para não varrer a base a cada tecla', () => {
    expect(termoBuscavel('')).toBe(false);
    expect(termoBuscavel(' a ')).toBe(false);
    expect(termoBuscavel('ab')).toBe(true);
    expect(termoBuscavel('000012')).toBe(true);
  });
});

describe('mesclarResultadosBusca', () => {
  it('remove duplicatas entre as consultas, pelo id da ocorrência', () => {
    const mesclado = mesclarResultadosBusca([[oc('1'), oc('2')], [oc('2'), oc('3')]]);
    expect(mesclado.map((o) => o.ocorrencia_id)).toEqual(['1', '2', '3']);
  });

  it('preserva a ordem das consultas: protocolo antes de natureza e endereço', () => {
    const porProtocolo = [oc('p1')];
    const porNatureza = [oc('n1')];
    const porEndereco = [oc('e1')];
    const mesclado = mesclarResultadosBusca([porProtocolo, porNatureza, porEndereco]);
    expect(mesclado.map((o) => o.ocorrencia_id)).toEqual(['p1', 'n1', 'e1']);
  });

  it('limita a quantidade devolvida', () => {
    const muitas = Array.from({ length: 30 }, (_, i) => oc(String(i)));
    expect(mesclarResultadosBusca([muitas])).toHaveLength(MAXIMO_RESULTADOS_BUSCA);
    expect(mesclarResultadosBusca([muitas], 3)).toHaveLength(3);
  });

  it('tolera consultas que falharam ou vieram vazias', () => {
    expect(mesclarResultadosBusca([[], [oc('1')], []])).toHaveLength(1);
    expect(mesclarResultadosBusca([])).toEqual([]);
  });
});

describe('separarTermos', () => {
  it('quebra a entrada em palavras, ignorando espaços repetidos', () => {
    expect(separarTermos('roubo andradas')).toEqual(['roubo', 'andradas']);
    expect(separarTermos('  furto   av   brasil ')).toEqual(['furto', 'av', 'brasil']);
  });

  it('devolve um único termo quando não há espaço', () => {
    expect(separarTermos('000004')).toEqual(['000004']);
  });

  it('limita a quantidade de termos, para não multiplicar as consultas', () => {
    expect(separarTermos('a b c d e f g')).toHaveLength(MAXIMO_TERMOS_BUSCA);
  });

  it('devolve lista vazia quando não há nada buscável', () => {
    expect(separarTermos('   ')).toEqual([]);
    expect(separarTermos('')).toEqual([]);
  });
});

describe('intersectarResultados', () => {
  it('devolve só as ocorrências que casaram com todos os termos', () => {
    const porRoubo = [oc('1'), oc('2'), oc('3')];
    const porAndradas = [oc('2'), oc('9')];
    expect(intersectarResultados([porRoubo, porAndradas]).map((o) => o.ocorrencia_id)).toEqual(['2']);
  });

  it('mantém a ordem do primeiro termo', () => {
    const primeiro = [oc('3'), oc('1'), oc('2')];
    const segundo = [oc('1'), oc('2'), oc('3')];
    expect(intersectarResultados([primeiro, segundo]).map((o) => o.ocorrencia_id)).toEqual(['3', '1', '2']);
  });

  it('com um termo só, comporta-se como a busca de palavra única', () => {
    expect(intersectarResultados([[oc('1'), oc('2')]]).map((o) => o.ocorrencia_id)).toEqual(['1', '2']);
  });

  it('um termo sem resultado zera a busca inteira', () => {
    expect(intersectarResultados([[oc('1')], []])).toEqual([]);
  });

  it('limita a quantidade devolvida', () => {
    const muitas = Array.from({ length: 30 }, (_, i) => oc(String(i)));
    expect(intersectarResultados([muitas])).toHaveLength(MAXIMO_RESULTADOS_BUSCA);
    expect(intersectarResultados([muitas], 2)).toHaveLength(2);
  });

  it('sem termos, não devolve nada', () => {
    expect(intersectarResultados([])).toEqual([]);
  });
});
