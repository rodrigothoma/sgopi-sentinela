import { describe, expect, it } from 'vitest';
import { aplicarFiltrosNaApi, escreverFiltrosNaUrl, lerFiltrosDaUrl, temFiltroAtivo } from '../filtrosOcorrencias';

describe('filtros de ocorrências na URL', () => {
  it('lê e escreve preservando outros parâmetros', () => {
    const url = escreverFiltrosNaUrl(new URLSearchParams('ocorrencia=abc&texto=velho'), { protocolo: ' OC-1 ', dataFatoDe: '2026-10-01', texto: '' });
    expect(url.get('ocorrencia')).toBe('abc');
    expect(url.get('protocolo')).toBe('OC-1');
    expect(url.get('de')).toBe('2026-10-01');
    expect(url.has('texto')).toBe(false);
    expect(lerFiltrosDaUrl(url)).toEqual({ protocolo: 'OC-1', dataFatoDe: '2026-10-01' });
  });

  it('descarta origem desconhecida', () => {
    expect(lerFiltrosDaUrl(new URLSearchParams('origem=XPTO'))).toEqual({});
  });

  it('detecta filtro ativo', () => {
    expect(temFiltroAtivo({})).toBe(false);
    expect(temFiltroAtivo({ texto: '  ' })).toBe(false);
    expect(temFiltroAtivo({ natureza: 'Furto' })).toBe(true);
  });
});

describe('filtros de ocorrências na API', () => {
  it('converte o dia local em instantes ISO do início e do fim do dia', () => {
    const p = aplicarFiltrosNaApi(new URLSearchParams(), { dataFatoDe: '2026-10-01', dataFatoAte: '2026-10-02', origem: 'PUBLICA', texto: ' praça ' });
    expect(p.get('data_fato_de')).toBe(new Date('2026-10-01T00:00:00').toISOString());
    expect(p.get('data_fato_ate')).toBe(new Date('2026-10-02T23:59:59.999').toISOString());
    expect(p.get('origem')).toBe('PUBLICA');
    expect(p.get('texto')).toBe('praça');
    expect(p.has('natureza')).toBe(false);
  });
});
