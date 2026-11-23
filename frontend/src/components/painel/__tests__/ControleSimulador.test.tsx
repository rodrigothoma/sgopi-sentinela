import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it, vi } from 'vitest';
import { ControleSimulador } from '../ControleSimulador';
import type { StatusSimuladorCompleto } from '../../../types/api';

vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (chave: string, params?: Record<string, number>) => params ? `${chave} ${params.despachados}/${params.encerrados}` : chave }),
}));

const status: StatusSimuladorCompleto = {
  ligado: false, intervalo_segundos: 1, raio_metros: 150, ticks: 7, posicoes_emitidas: 5,
  orquestrador: { ligado: false, intervalo_segundos: 5, janela_carencia_segundos: 20, tempo_atendimento_segundos: 45, ticks: 3, ocioso: 1, despachados: 2, encerrados: 1 },
};
const alternar = async (): Promise<void> => {};

// A renderização estática confere condições, classes e textos sem instalar um ambiente DOM.
describe('controle do simulador', () => {
  it('não oferece controles sem permissão ou antes da carga do status', () => {
    expect(renderToStaticMarkup(<ControleSimulador podeDespachar={false} simulador={status} onAlternar={alternar} />)).toBe('');
    expect(renderToStaticMarkup(<ControleSimulador podeDespachar simulador={null} onAlternar={alternar} />)).toBe('');
  });

  it('mantém o botão de ligar com o contador e sem badge automático', () => {
    const html = renderToStaticMarkup(<ControleSimulador podeDespachar simulador={status} onAlternar={alternar} />);
    expect(html).toContain('btn-primary');
    expect(html).toContain('painel:simulador.ligar');
    expect(html).toContain('(7)');
    expect(html).not.toContain('badge-OK');
  });

  it('mantém o botão de desligar e os contadores do orquestrador ligado', () => {
    const ligado = { ...status, ligado: true, orquestrador: { ...status.orquestrador, ligado: true } };
    const html = renderToStaticMarkup(<ControleSimulador podeDespachar simulador={ligado} onAlternar={alternar} />);
    expect(html).toContain('btn-warn');
    expect(html).toContain('painel:simulador.desligar');
    expect(html).toContain('badge-OK');
    expect(html).toContain('painel:simulador.despacho_contador 2/1');
  });
});
