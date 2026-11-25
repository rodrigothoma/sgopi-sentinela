import { describe, expect, it } from 'vitest';
import {
  GRUPOS_FILA_DELEGADO,
  abaDoStatus,
  idOcorrenciaLegada,
  lerAba,
  urlDaLista,
  urlDoDetalhe,
} from '../ocorrenciaDeepLink';

describe('deep links de ocorrências', () => {
  it('abre o detalhe preservando filtros e aba, sem deixar o parâmetro legado', () => {
    const params = new URLSearchParams('ocorrencia=abc&protocolo=SGOPI-1&aba=2&texto=furto');
    expect(urlDoDetalhe('/fila', 'id com espaço', params)).toBe('/fila/id%20com%20espa%C3%A7o?protocolo=SGOPI-1&aba=2&texto=furto');
  });

  it('volta para a lista com os filtros e a aba calculada pelo status', () => {
    const params = new URLSearchParams('protocolo=SGOPI-1&aba=0&ocorrencia=abc');
    expect(urlDaLista('/fila', params, 3)).toBe('/fila?protocolo=SGOPI-1&aba=3');
    expect(urlDaLista('/minhas', params)).toBe('/minhas?protocolo=SGOPI-1');
  });

  it('lê a aba apenas quando ela é um índice válido', () => {
    expect(lerAba(new URLSearchParams('aba=2'), 3)).toBe(2);
    expect(lerAba(new URLSearchParams('aba=9'), 3)).toBe(0);
    expect(lerAba(new URLSearchParams('aba=x'), 3)).toBe(0);
    expect(lerAba(new URLSearchParams(), 3)).toBe(0);
  });

  it('localiza a aba do status da fila e usa a primeira como fallback', () => {
    expect(abaDoStatus('EM_ATENDIMENTO', GRUPOS_FILA_DELEGADO)).toBe(2);
    expect(abaDoStatus('CANCELADA' as never, GRUPOS_FILA_DELEGADO)).toBe(0);
  });

  it('lê o link legado sem espaços', () => {
    expect(idOcorrenciaLegada(new URLSearchParams('ocorrencia=%20abc%20'))).toBe('abc');
    expect(idOcorrenciaLegada(new URLSearchParams('protocolo=SGOPI-1'))).toBeNull();
  });
});
