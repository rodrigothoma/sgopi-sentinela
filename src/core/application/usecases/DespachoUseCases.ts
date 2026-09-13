import { ErroNaoEncontrado, ErroPreCondicao } from "@/core/domain/shared/DomainError";
import { type Coordenada, distanciaHaversineKm } from "@/core/domain/shared/Coordenada";
import { Viatura } from "@/core/domain/viatura/Viatura";
import { ModoDespacho, type OrdemDespacho } from "@/core/domain/despacho/OrdemDespacho";
import type { Ator } from "../seguranca/Ator";
import { Acao } from "../seguranca/PoliticaAutorizacao";
import type { Autorizador } from "../seguranca/Autorizador";
import type { RepositorioDespachos, RepositorioOcorrencias, RepositorioViaturas } from "../ports/outbound/Repositorios";
import type { PortaAuditoria, PortaGeradorId, PortaRelogio, PublicadorEventos } from "../ports/outbound/Infraestrutura";
import type {
  AtualizarTelemetriaViatura,
  ComandoDespachar,
  ConsultarDespachos,
  ConsultarViaturas,
  DespacharViatura,
  ResultadoSugestao,
  SugerirViaturasProximas,
  SugestaoViatura,
  ViaturaComSinal,
} from "../ports/inbound/CasosDeUso";
import type { EventoOcorrenciaAlterada, EventoViaturaDespachada, EventoViaturaPosicao } from "./Eventos";

export interface DependenciasDespacho {
  readonly ocorrencias: RepositorioOcorrencias;
  readonly viaturas: RepositorioViaturas;
  readonly despachos: RepositorioDespachos;
  readonly auditoria: PortaAuditoria;
  readonly relogio: PortaRelogio;
  readonly ids: PortaGeradorId;
  readonly eventos: PublicadorEventos;
  readonly autorizador: Autorizador;
}

function comSinal(v: Viatura, agora: Date): ViaturaComSinal {
  return { ...v.paraEstado(), sinalGpsValido: v.sinalGpsValido(agora) };
}

export class ConsultarViaturasUseCase implements ConsultarViaturas {
  constructor(private readonly d: DependenciasDespacho) {}
  async listar(ator: Ator): Promise<ViaturaComSinal[]> {
    await this.d.autorizador.exigir(ator, Acao.VIATURA_CONSULTAR, { tipo: "viatura", id: "*" });
    const agora = this.d.relogio.agora();
    return (await this.d.viaturas.listar()).map((v) => comSinal(v, agora));
  }
}

/** Porta de entrada da telemetria (simulador no MVP; hardware real no futuro). */
export class AtualizarTelemetriaUseCase implements AtualizarTelemetriaViatura {
  constructor(private readonly d: DependenciasDespacho) {}

  async executar(ator: Ator, viaturaId: string, coordenada: Coordenada, recebidaEm?: Date): Promise<void> {
    await this.d.autorizador.exigir(ator, Acao.VIATURA_TELEMETRIA, { tipo: "viatura", id: viaturaId });
    const v = await this.d.viaturas.obterPorId(viaturaId);
    if (!v) throw new ErroNaoEncontrado("Viatura", viaturaId);

    const em = recebidaEm ?? this.d.relogio.agora();
    const atualizada = v.atualizarPosicao(coordenada, em);
    await this.d.viaturas.salvar(atualizada);

    const evento: EventoViaturaPosicao = {
      tipo: "viatura.posicao",
      ocorridoEm: em,
      payload: { viaturaId, prefixo: v.prefixo, status: atualizada.status, coordenada, recebidaEm: em.toISOString() },
    };
    this.d.eventos.publicar(evento);
    // Telemetria não é auditada individualmente (volume alto); apenas o despacho é.
  }
}

/** UC02 passo 4 — ordena viaturas disponíveis pela distância geodésica. */
export class SugerirViaturasProximasUseCase implements SugerirViaturasProximas {
  constructor(private readonly d: DependenciasDespacho) {}

  async executar(ator: Ator, ocorrenciaId: string, limite = 3): Promise<ResultadoSugestao> {
    await this.d.autorizador.exigir(ator, Acao.DESPACHO_SUGERIR, { tipo: "ocorrencia", id: ocorrenciaId });
    const ocorrencia = await this.d.ocorrencias.obterPorId(ocorrenciaId);
    if (!ocorrencia) throw new ErroNaoEncontrado("Ocorrência", ocorrenciaId);
    if (!ocorrencia.podeSerDespachada()) {
      throw new ErroPreCondicao("Somente ocorrências VALIDADAS podem ser despachadas.", { status: ocorrencia.status });
    }

    const agora = this.d.relogio.agora();
    const disponiveis = (await this.d.viaturas.listar()).filter((v) => v.estaDisponivel());
    const alvo = ocorrencia.coordenada;

    const sugestoes: SugestaoViatura[] = disponiveis.map((v) => {
      const sinalOk = v.sinalGpsValido(agora);
      const distanciaKm =
        alvo && sinalOk && v.ultimaPosicao ? distanciaHaversineKm(alvo, v.ultimaPosicao.coordenada) : null;
      return { viatura: comSinal(v, agora), distanciaKm };
    });

    // GPS válido primeiro (por distância); sem sinal ao final (RNF04: fallback manual).
    sugestoes.sort((a, b) => {
      if (a.distanciaKm === null && b.distanciaKm === null) return 0;
      if (a.distanciaKm === null) return 1;
      if (b.distanciaKm === null) return -1;
      return a.distanciaKm - b.distanciaKm;
    });

    const algumaComGps = sugestoes.some((s) => s.distanciaKm !== null);
    return {
      ocorrenciaId,
      coordenadaOcorrencia: alvo,
      despachoAutomaticoBloqueado: disponiveis.length > 0 && !algumaComGps,
      sugestoes: sugestoes.slice(0, limite),
    };
  }
}

/** UC02 passos 5–9 — emite a ordem de despacho. */
export class DespacharViaturaUseCase implements DespacharViatura {
  constructor(private readonly d: DependenciasDespacho) {}

  async executar(ator: Ator, cmd: ComandoDespachar): Promise<OrdemDespacho> {
    await this.d.autorizador.exigir(ator, Acao.DESPACHO_EMITIR, { tipo: "ocorrencia", id: cmd.ocorrenciaId });

    const [ocorrencia, viatura] = await Promise.all([
      this.d.ocorrencias.obterPorId(cmd.ocorrenciaId),
      this.d.viaturas.obterPorId(cmd.viaturaId),
    ]);
    if (!ocorrencia) throw new ErroNaoEncontrado("Ocorrência", cmd.ocorrenciaId);
    if (!viatura) throw new ErroNaoEncontrado("Viatura", cmd.viaturaId);

    const agora = this.d.relogio.agora();
    const gpsValido = viatura.sinalGpsValido(agora);

    // RNF04 / UC02 Exceção I: sem GPS válido, o despacho automático é bloqueado;
    // o operador precisa informar a posição (rádio) para prosseguir manualmente.
    if (!gpsValido && !cmd.posicaoInformada) {
      throw new ErroPreCondicao(
        `Viatura ${viatura.prefixo} sem sinal GPS válido (> 60 s). Informe a posição via rádio para despacho manual.`,
        { viaturaId: viatura.id, motivo: "GPS_DESATUALIZADO" },
      );
    }

    const posicaoRef = gpsValido ? viatura.ultimaPosicao!.coordenada : cmd.posicaoInformada!;
    const distanciaKm = ocorrencia.coordenada ? distanciaHaversineKm(ocorrencia.coordenada, posicaoRef) : undefined;

    // As duas transições de domínio validam suas próprias pré-condições (RN1, RN2).
    const viaturaDespachada = viatura.despachar(ocorrencia.id);
    const ocorrenciaEmAtendimento = ocorrencia.iniciarAtendimento(ator.id, agora);

    const ordem: OrdemDespacho = {
      id: this.d.ids.gerar(),
      ocorrenciaId: ocorrencia.id,
      protocoloOcorrencia: ocorrencia.protocolo,
      viaturaId: viatura.id,
      prefixoViatura: viatura.prefixo,
      operadorId: ator.id,
      emitidaEm: agora,
      modo: gpsValido ? ModoDespacho.AUTOMATICO : ModoDespacho.MANUAL_POSICAO_INFORMADA,
      distanciaKm,
      posicaoInformada: gpsValido ? undefined : cmd.posicaoInformada,
      observacao: cmd.observacao,
    };

    // Sem transação distribuída no MVP: ordem de gravação escolhida para que
    // uma falha deixe o sistema consultável (ver docs/mvp/03-problemas-encontrados.md).
    await this.d.despachos.salvar(ordem);
    await this.d.viaturas.salvar(viaturaDespachada);
    await this.d.ocorrencias.salvar(ocorrenciaEmAtendimento);

    // UC02 passo 9 — auditoria com carimbo de data/hora.
    await this.d.auditoria.registrar({
      atorId: ator.id, atorPapel: ator.papel, acao: Acao.DESPACHO_EMITIR,
      recursoTipo: "ordem_despacho", recursoId: ordem.id, resultado: "SUCESSO",
      detalhes: { ocorrenciaId: ordem.ocorrenciaId, protocolo: ordem.protocoloOcorrencia, viaturaId: ordem.viaturaId, modo: ordem.modo, distanciaKm },
    });

    // UC02 passo 8 — transmissão em tempo real (SSE) para o painel/terminal da viatura.
    const evDespacho: EventoViaturaDespachada = {
      tipo: "viatura.despachada", ocorridoEm: agora,
      payload: { viaturaId: viatura.id, prefixo: viatura.prefixo, ocorrenciaId: ocorrencia.id, protocolo: ocorrencia.protocolo, ordemId: ordem.id },
    };
    const evOcorrencia: EventoOcorrenciaAlterada = {
      tipo: "ocorrencia.alterada", ocorridoEm: agora,
      payload: { ocorrenciaId: ocorrencia.id, protocolo: ocorrencia.protocolo, status: ocorrenciaEmAtendimento.status, gravidade: ocorrencia.gravidade, coordenada: ocorrencia.coordenada },
    };
    this.d.eventos.publicar(evDespacho);
    this.d.eventos.publicar(evOcorrencia);
    return ordem;
  }
}

export class ConsultarDespachosUseCase implements ConsultarDespachos {
  constructor(private readonly d: DependenciasDespacho) {}
  async listar(ator: Ator): Promise<OrdemDespacho[]> {
    await this.d.autorizador.exigir(ator, Acao.DESPACHO_SUGERIR, { tipo: "ordem_despacho", id: "*" });
    return (await this.d.despachos.listar()).sort((a, b) => b.emitidaEm.getTime() - a.emitidaEm.getTime());
  }
}
