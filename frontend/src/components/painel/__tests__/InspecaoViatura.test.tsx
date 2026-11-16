import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it, vi } from 'vitest';
import { InspecaoViatura } from '../InspecaoViatura';
import type { Viatura } from '../../../types/api';

vi.mock('react-i18next', () => ({ useTranslation: () => ({ t: (chave: string) => chave }) }));
vi.mock('../../../utils/datas', () => ({ formatarDataHora: (valor: string) => valor }));

const viatura: Viatura = {
  id: 'v1', prefixo: 'VTR-01', placa: 'ABC1D23', situacao: 'DISPONIVEL', sinal: 'OK',
  latitude: -29.78, longitude: -55.79, posicao_registrada_em: '2026-11-16T12:00:00Z', versao: 1,
};
const acao = (): void => {};
const renderizar = (v: Viatura, mapaDisponivel = true): string => renderToStaticMarkup(
  <InspecaoViatura viatura={v} mapaDisponivel={mapaDisponivel} onCentralizar={acao} onFechar={acao} />,
);

describe('card de inspeção', () => {
  it('exibe o responsável informado no cadastro', () => {
    expect(renderizar({ ...viatura, responsavel: 'Ana Souza' })).toContain('Ana Souza');
  });
  it('informa quando não há responsável', () => {
    expect(renderizar(viatura)).toContain('inspecao.sem_responsavel');
  });
  it('exibe identidade, posição e badges e permite centralizar uma posição conhecida', () => {
    const html = renderizar(viatura);
    expect(html).toContain('VTR-01');
    expect(html).toContain('ABC1D23');
    expect(html).toContain('-29.78000, -55.79000');
    expect(html).toContain('badge-DISPONIVEL');
    expect(html).toContain('badge-OK');
    expect(html).not.toContain('disabled');
  });

  it('reflete os dados atuais em vez de preservar uma cópia da viatura', () => {
    const html = renderizar({ ...viatura, situacao: 'EM_DESLOCAMENTO', latitude: -29.77 });
    expect(html).toContain('badge-EM_DESLOCAMENTO');
    expect(html).toContain('-29.77000, -55.79000');
    expect(html).not.toContain('badge-DISPONIVEL');
  });

  it('explica por que não se pode centralizar uma unidade sem posição', () => {
    const html = renderizar({ ...viatura, latitude: null, longitude: null, posicao_registrada_em: null, sinal: 'SEM_POSICAO' });
    expect(html).toContain('inspecao.sem_posicao');
    expect(html).toContain('inspecao.sem_registro');
    expect(html).toContain('disabled');
    expect(html).toContain('aria-describedby="inspecao-motivo"');
  });

  it('mantém os dados e explica a indisponibilidade do mapa', () => {
    const html = renderizar(viatura, false);
    expect(html).toContain('ABC1D23');
    expect(html).toContain('inspecao.mapa_indisponivel');
    expect(html).toContain('disabled');
  });

  it('identifica posição desatualizada sem apagar a última coordenada conhecida', () => {
    const html = renderizar({ ...viatura, sinal: 'SEM_SINAL' });
    expect(html).toContain('inspecao.posicao_desatualizada');
    expect(html).toContain('-29.78000, -55.79000');
    expect(html).not.toContain('disabled');
  });
});
