import type { AtualizarTelemetriaViatura, ConsultarViaturas } from "@/core/application/ports/inbound/CasosDeUso";
import { ATOR_SISTEMA } from "@/core/application/seguranca/Ator";
import { criarCoordenada, type Coordenada } from "@/core/domain/shared/Coordenada";

export interface OpcoesSimulador {
  readonly centro: Coordenada;
  readonly intervaloMs: number;
  /** IDs de viaturas que "perdem sinal" ciclicamente para exercitar o RNF04. */
  readonly viaturasComFalhaIntermitente: readonly string[];
}

/**
 * Adaptador de ENTRADA (driver): substitui o hardware GPS real (Seção 3.2 —
 * limites do MVP). Move cada viatura em passeio aleatório suave ao redor do
 * centro e alimenta o núcleo pela mesma porta que o hardware usaria.
 */
export class SimuladorGps {
  private timer: ReturnType<typeof setInterval> | null = null;
  private tick = 0;
  private readonly posicoes = new Map<string, Coordenada>();
  private readonly rumos = new Map<string, number>();

  constructor(
    private readonly telemetria: AtualizarTelemetriaViatura,
    private readonly viaturas: ConsultarViaturas,
    private readonly opcoes: OpcoesSimulador,
  ) {}

  iniciar(): void {
    if (this.timer) return;
    void this.passo();
    this.timer = setInterval(() => void this.passo(), this.opcoes.intervaloMs);
    // Não segurar o processo vivo por causa do simulador (encerramento limpo).
    if (typeof this.timer === "object" && "unref" in this.timer) this.timer.unref();
  }

  parar(): void {
    if (this.timer) clearInterval(this.timer);
    this.timer = null;
  }

  get ativo(): boolean {
    return this.timer !== null;
  }

  private async passo(): Promise<void> {
    this.tick += 1;
    try {
      const lista = await this.viaturas.listar(ATOR_SISTEMA);
      for (const v of lista) {
        if (v.status === "INDISPONIVEL") continue;
        // Falha intermitente: 40 ticks com sinal, 40 ticks sem (≈ 80 s / 80 s a 2 s por tick).
        if (this.opcoes.viaturasComFalhaIntermitente.includes(v.id) && Math.floor(this.tick / 40) % 2 === 1) continue;

        const proxima = this.proximaPosicao(v.id);
        await this.telemetria.executar(ATOR_SISTEMA, v.id, proxima);
      }
    } catch (erro) {
      // RNF04: erro no simulador é logado e a próxima iteração tenta de novo.
      console.error("[simulador-gps] falha no tick", this.tick, erro);
    }
  }

  private proximaPosicao(viaturaId: string): Coordenada {
    const atual = this.posicoes.get(viaturaId) ?? this.posicaoInicial(viaturaId);
    const rumoAnterior = this.rumos.get(viaturaId) ?? Math.random() * 2 * Math.PI;
    const rumo = rumoAnterior + (Math.random() - 0.5) * 0.8; // curva suave
    const passoGraus = 0.00035; // ≈ 35 m por tick

    let lat = atual.latitude + Math.sin(rumo) * passoGraus;
    let lng = atual.longitude + Math.cos(rumo) * passoGraus;

    // Mantém dentro de um raio de ~2,5 km do centro ("cerca" da cidade).
    const dLat = lat - this.opcoes.centro.latitude;
    const dLng = lng - this.opcoes.centro.longitude;
    if (Math.hypot(dLat, dLng) > 0.025) {
      lat = atual.latitude - dLat * 0.05;
      lng = atual.longitude - dLng * 0.05;
      this.rumos.set(viaturaId, rumo + Math.PI);
    } else {
      this.rumos.set(viaturaId, rumo);
    }

    const c = criarCoordenada(lat, lng);
    this.posicoes.set(viaturaId, c);
    return c;
  }

  private posicaoInicial(viaturaId: string): Coordenada {
    // Espalha as viaturas de forma determinística pelo índice do id.
    const semente = [...viaturaId].reduce((s, ch) => s + ch.charCodeAt(0), 0);
    const ang = (semente % 360) * (Math.PI / 180);
    const raio = 0.008 + (semente % 7) * 0.002;
    return criarCoordenada(this.opcoes.centro.latitude + Math.sin(ang) * raio, this.opcoes.centro.longitude + Math.cos(ang) * raio);
  }
}
