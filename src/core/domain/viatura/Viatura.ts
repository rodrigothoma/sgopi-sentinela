import { ErroPreCondicao } from "../shared/DomainError";
import type { Coordenada } from "../shared/Coordenada";

export const StatusViatura = {
  DISPONIVEL: "DISPONIVEL",
  EM_DESLOCAMENTO: "EM_DESLOCAMENTO",
  EM_ATENDIMENTO: "EM_ATENDIMENTO",
  INDISPONIVEL: "INDISPONIVEL",
} as const;
export type StatusViatura = (typeof StatusViatura)[keyof typeof StatusViatura];

export interface PosicaoGps {
  readonly coordenada: Coordenada;
  readonly recebidaEm: Date;
}

export interface EstadoViatura {
  readonly id: string;
  readonly prefixo: string;
  readonly placa: string;
  readonly equipe: string;
  readonly status: StatusViatura;
  readonly ultimaPosicao?: PosicaoGps;
  readonly ocorrenciaAtualId?: string;
}

/** UC02 RN3: coordenada válida = recebida nos últimos 60 s. */
export const TOLERANCIA_SINAL_GPS_MS = 60_000;

export class Viatura {
  private constructor(private readonly estado: EstadoViatura) {}

  static reidratar(estado: EstadoViatura): Viatura {
    return new Viatura(estado);
  }

  get id(): string { return this.estado.id; }
  get prefixo(): string { return this.estado.prefixo; }
  get status(): StatusViatura { return this.estado.status; }
  get ultimaPosicao(): PosicaoGps | undefined { return this.estado.ultimaPosicao; }

  paraEstado(): EstadoViatura {
    return { ...this.estado };
  }

  estaDisponivel(): boolean {
    return this.estado.status === StatusViatura.DISPONIVEL;
  }

  /** RNF04 / UC02 Exceção I: sinal desatualizado (> 60 s) ou inexistente. */
  sinalGpsValido(agora: Date): boolean {
    const p = this.estado.ultimaPosicao;
    if (!p) return false;
    return agora.getTime() - p.recebidaEm.getTime() <= TOLERANCIA_SINAL_GPS_MS;
  }

  atualizarPosicao(coordenada: Coordenada, recebidaEm: Date): Viatura {
    // Rejeita telemetria mais antiga que a já conhecida (pacotes fora de ordem).
    const atual = this.estado.ultimaPosicao;
    if (atual && recebidaEm.getTime() < atual.recebidaEm.getTime()) {
      return this;
    }
    return new Viatura({ ...this.estado, ultimaPosicao: { coordenada, recebidaEm } });
  }

  /** UC02 passo 7. Apenas viaturas DISPONÍVEL recebem despacho (RN1). */
  despachar(ocorrenciaId: string): Viatura {
    if (!this.estaDisponivel()) {
      throw new ErroPreCondicao(`Viatura ${this.estado.prefixo} não está disponível.`, {
        status: this.estado.status,
      });
    }
    return new Viatura({ ...this.estado, status: StatusViatura.EM_DESLOCAMENTO, ocorrenciaAtualId: ocorrenciaId });
  }

  chegarAoLocal(): Viatura {
    if (this.estado.status !== StatusViatura.EM_DESLOCAMENTO) {
      throw new ErroPreCondicao("Viatura não está em deslocamento.");
    }
    return new Viatura({ ...this.estado, status: StatusViatura.EM_ATENDIMENTO });
  }

  liberar(): Viatura {
    return new Viatura({ ...this.estado, status: StatusViatura.DISPONIVEL, ocorrenciaAtualId: undefined });
  }
}
