import { ErroPreCondicao, ErroValidacao } from "../shared/DomainError";
import type { Coordenada } from "../shared/Coordenada";
import { type Envolvido, validarEnvolvido } from "./Envolvido";
import type { EvidenciaDigital } from "./EvidenciaDigital";
import { StatusOcorrencia, assegurarTransicao } from "./StatusOcorrencia";

export interface Endereco {
  readonly logradouro: string;
  readonly numero?: string;
  readonly bairro: string;
  readonly cidade: string;
  readonly uf: string;
}

export interface TransicaoStatus {
  readonly de: StatusOcorrencia | null;
  readonly para: StatusOcorrencia;
  readonly em: Date;
  readonly autorId: string;
  readonly motivo?: string;
}

export interface DadosNovaOcorrencia {
  readonly id: string;
  readonly protocolo: string;
  readonly tipificacao: string;
  readonly descricaoFato: string;
  readonly endereco: Endereco;
  readonly coordenada?: Coordenada;
  readonly envolvidos: readonly Envolvido[];
  readonly evidencias: readonly EvidenciaDigital[];
  readonly agenteId: string;
  readonly gravidade: Gravidade;
  readonly criadaEm: Date;
}

export const Gravidade = { BAIXA: 1, MEDIA: 2, ALTA: 3, CRITICA: 4 } as const;
export type Gravidade = (typeof Gravidade)[keyof typeof Gravidade];

export interface EstadoOcorrencia {
  readonly id: string;
  readonly protocolo: string;
  readonly tipificacao: string;
  readonly descricaoFato: string;
  readonly endereco: Endereco;
  readonly coordenada?: Coordenada;
  readonly envolvidos: readonly Envolvido[];
  readonly evidencias: readonly EvidenciaDigital[];
  readonly agenteId: string;
  readonly gravidade: Gravidade;
  readonly status: StatusOcorrencia;
  readonly criadaEm: Date;
  readonly atualizadaEm: Date;
  readonly historico: readonly TransicaoStatus[];
  /** Preenchidos pelo Delegado (UC04). */
  readonly delegadoId?: string;
  readonly despachoAutoridade?: string;
  readonly pendenciasCorrecao?: string;
  /** Hash da narrativa no momento da validação — impede edição posterior (UC04 RN2). */
  readonly hashIntegridade?: string;
  readonly validadaEm?: Date;
}

/**
 * Agregado raiz. Toda mutação passa por métodos que garantem os invariantes.
 * A classe é imutável do ponto de vista externo: cada método devolve uma
 * nova instância (facilita auditoria e testes).
 */
export class Ocorrencia {
  private constructor(private readonly estado: EstadoOcorrencia) {}

  static registrar(dados: DadosNovaOcorrencia): Ocorrencia {
    Ocorrencia.validarDadosBasicos(dados);
    const estado: EstadoOcorrencia = {
      ...dados,
      // UC01 RN3: toda ocorrência recém-criada assume compulsoriamente este status.
      status: StatusOcorrencia.AGUARDANDO_REVISAO,
      atualizadaEm: dados.criadaEm,
      historico: [
        {
          de: null,
          para: StatusOcorrencia.AGUARDANDO_REVISAO,
          em: dados.criadaEm,
          autorId: dados.agenteId,
        },
      ],
    };
    return new Ocorrencia(estado);
  }

  /** Reidrata a partir da persistência sem revalidar (o estado já foi validado ao nascer). */
  static reidratar(estado: EstadoOcorrencia): Ocorrencia {
    return new Ocorrencia(estado);
  }

  private static validarDadosBasicos(d: DadosNovaOcorrencia): void {
    const faltantes: string[] = [];
    if (!d.tipificacao?.trim()) faltantes.push("tipificacao");
    if (!d.descricaoFato || d.descricaoFato.trim().length < 20) faltantes.push("descricaoFato");
    if (!d.endereco?.logradouro?.trim()) faltantes.push("endereco.logradouro");
    if (!d.endereco?.bairro?.trim()) faltantes.push("endereco.bairro");
    if (!d.endereco?.cidade?.trim()) faltantes.push("endereco.cidade");
    if (!d.endereco?.uf || d.endereco.uf.trim().length !== 2) faltantes.push("endereco.uf");
    // UC01 RN1: qualificação de no mínimo um envolvido é obrigatória.
    if (!d.envolvidos || d.envolvidos.length === 0) faltantes.push("envolvidos");
    if (faltantes.length > 0) {
      throw new ErroValidacao("Campos obrigatórios não preenchidos.", { camposFaltantes: faltantes });
    }
    d.envolvidos.forEach(validarEnvolvido);
  }

  // ---------- Consultas ----------
  get id(): string { return this.estado.id; }
  get protocolo(): string { return this.estado.protocolo; }
  get status(): StatusOcorrencia { return this.estado.status; }
  get agenteId(): string { return this.estado.agenteId; }
  get coordenada(): Coordenada | undefined { return this.estado.coordenada; }
  get gravidade(): Gravidade { return this.estado.gravidade; }
  get descricaoFato(): string { return this.estado.descricaoFato; }
  get criadaEm(): Date { return this.estado.criadaEm; }

  /** Snapshot imutável para persistência/apresentação. */
  paraEstado(): EstadoOcorrencia {
    return { ...this.estado, envolvidos: [...this.estado.envolvidos], evidencias: [...this.estado.evidencias], historico: [...this.estado.historico] };
  }

  podeSerDespachada(): boolean {
    // UC02 RN2: apenas ocorrências validadas pelo Delegado podem ser despachadas.
    return this.estado.status === StatusOcorrencia.VALIDADA;
  }

  // ---------- Comandos ----------

  /**
   * UC04 — validação pelo Delegado. `hashNarrativa` é calculado pelo caso de
   * uso via PortaHash e sela a narrativa contra edições diretas (RN2).
   */
  validar(delegadoId: string, despachoAutoridade: string, hashNarrativa: string, em: Date): Ocorrencia {
    if (!despachoAutoridade?.trim()) {
      throw new ErroValidacao("O despacho da autoridade é obrigatório para validar.");
    }
    return this.transitar(StatusOcorrencia.VALIDADA, delegadoId, em, despachoAutoridade, {
      delegadoId,
      despachoAutoridade,
      hashIntegridade: hashNarrativa,
      validadaEm: em,
      pendenciasCorrecao: undefined,
    });
  }

  /** UC04 — Cenário Alternativo I: devolução para correção (justificativa obrigatória — RN3). */
  devolverParaCorrecao(delegadoId: string, pendencias: string, em: Date): Ocorrencia {
    if (!pendencias || pendencias.trim().length < 10) {
      throw new ErroValidacao("A justificativa técnica da devolução é obrigatória (mín. 10 caracteres).");
    }
    return this.transitar(StatusOcorrencia.EM_CORRECAO, delegadoId, em, pendencias, {
      delegadoId,
      pendenciasCorrecao: pendencias,
    });
  }

  /** Agente corrige a narrativa e reenvia para revisão. Só é permitido em EM_CORRECAO. */
  corrigirEReenviar(agenteId: string, novaDescricao: string, em: Date): Ocorrencia {
    if (agenteId !== this.estado.agenteId) {
      throw new ErroPreCondicao("Apenas o agente autor pode corrigir a ocorrência.");
    }
    if (this.estado.hashIntegridade) {
      throw new ErroPreCondicao("Narrativa selada por validação; edição direta não é permitida (RNF03).");
    }
    if (!novaDescricao || novaDescricao.trim().length < 20) {
      throw new ErroValidacao("A descrição do fato deve ter ao menos 20 caracteres.");
    }
    return this.transitar(StatusOcorrencia.AGUARDANDO_REVISAO, agenteId, em, "Correção reenviada", {
      descricaoFato: novaDescricao,
      pendenciasCorrecao: undefined,
    });
  }

  /** UC02 passo 7. */
  iniciarAtendimento(operadorId: string, em: Date): Ocorrencia {
    if (!this.podeSerDespachada()) {
      throw new ErroPreCondicao("Somente ocorrências com status VALIDADA podem ser despachadas.", {
        statusAtual: this.estado.status,
      });
    }
    return this.transitar(StatusOcorrencia.EM_ATENDIMENTO, operadorId, em, "Viatura despachada");
  }

  concluir(autorId: string, em: Date): Ocorrencia {
    return this.transitar(StatusOcorrencia.CONCLUIDA, autorId, em);
  }

  private transitar(
    para: StatusOcorrencia,
    autorId: string,
    em: Date,
    motivo?: string,
    extras: Partial<EstadoOcorrencia> = {},
  ): Ocorrencia {
    assegurarTransicao(this.estado.status, para);
    return new Ocorrencia({
      ...this.estado,
      ...extras,
      status: para,
      atualizadaEm: em,
      historico: [...this.estado.historico, { de: this.estado.status, para, em, autorId, motivo }],
    });
  }
}
