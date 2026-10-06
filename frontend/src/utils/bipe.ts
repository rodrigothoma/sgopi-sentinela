/**
 * Destaque sonoro de alerta crítico (UC11, pós-condição 1).
 *
 * Gera o som pela Web Audio API em vez de carregar um arquivo: evita dependência
 * nova, requisição de rede e qualquer risco de o áudio não estar disponível.
 * Toda a execução é protegida — navegador sem suporte, ou que bloqueia áudio antes
 * de uma interação do usuário, apenas não emite som, sem quebrar a tela.
 */

type ContextoAudio = typeof AudioContext;

function obterContexto(): AudioContext | null {
  try {
    const Ctor: ContextoAudio | undefined =
      window.AudioContext ?? (window as unknown as { webkitAudioContext?: ContextoAudio }).webkitAudioContext;
    return Ctor ? new Ctor() : null;
  } catch {
    return null;
  }
}

/** Dois bipes curtos e descendentes — perceptível sem ser estridente numa central. */
export function tocarBipeAlerta(): void {
  const ctx = obterContexto();
  if (!ctx) return;

  try {
    const agora = ctx.currentTime;
    const tons = [
      { frequencia: 880, inicio: 0 },
      { frequencia: 660, inicio: 0.18 },
    ];

    for (const { frequencia, inicio } of tons) {
      const oscilador = ctx.createOscillator();
      const ganho = ctx.createGain();
      oscilador.type = 'sine';
      oscilador.frequency.setValueAtTime(frequencia, agora + inicio);

      // Envelope curto: sem o fade o navegador produz um "clique" no corte.
      ganho.gain.setValueAtTime(0.0001, agora + inicio);
      ganho.gain.exponentialRampToValueAtTime(0.25, agora + inicio + 0.02);
      ganho.gain.exponentialRampToValueAtTime(0.0001, agora + inicio + 0.16);

      oscilador.connect(ganho).connect(ctx.destination);
      oscilador.start(agora + inicio);
      oscilador.stop(agora + inicio + 0.18);
    }

    // Libera o contexto depois do último tom para não acumular instâncias.
    window.setTimeout(() => void ctx.close().catch(() => undefined), 800);
  } catch {
    void ctx.close().catch(() => undefined);
  }
}
