import { Ocorrencia, type EstadoOcorrencia } from "@/core/domain/ocorrencia/Ocorrencia";
import { validarFormatoEvidencia } from "@/core/domain/ocorrencia/EvidenciaDigital";
import { ErroNaoEncontrado } from "@/core/domain/shared/DomainError";
import type { StatusOcorrencia } from "@/core/domain/ocorrencia/StatusOcorrencia";
import type { Ator } from "../seguranca/Ator";
import { Acao } from "../seguranca/PoliticaAutorizacao";
import type { Autorizador } from "../seguranca/Autorizador";
import type { RepositorioOcorrencias } from "../ports/outbound/Repositorios";
import type { PortaAuditoria, PortaGeradorId, PortaHash, PortaRelogio, PublicadorEventos } from "../ports/outbound/Infraestrutura";
import type {
  ComandoRegistrarOcorrencia,
  ConsultarOcorrencias,
  CorrigirOcorrencia,
  DevolverOcorrenciaParaCorrecao,
  RegistrarOcorrencia,
  ValidarOcorrencia,
} from "../ports/inbound/CasosDeUso";
import type { EventoOcorrenciaAlterada } from "./Eventos";

export interface DependenciasOcorrencia {
  readonly ocorrencias: RepositorioOcorrencias;
  readonly auditoria: PortaAuditoria;
  readonly relogio: PortaRelogio;
  readonly ids: PortaGeradorId;
  readonly hash: PortaHash;
  readonly eventos: PublicadorEventos;
  readonly autorizador: Autorizador;
}

function eventoAlterada(o: Ocorrencia, em: Date): EventoOcorrenciaAlterada {
  return {
    tipo: "ocorrencia.alterada",
    ocorridoEm: em,
    payload: { ocorrenciaId: o.id, protocolo: o.protocolo, status: o.status, gravidade: o.gravidade, coordenada: o.coordenada },
  };
}

/** UC01 — Registrar Ocorrência Policial. */
export class RegistrarOcorrenciaUseCase implements RegistrarOcorrencia {
  constructor(private readonly d: DependenciasOcorrencia) {}

  async executar(ator: Ator, cmd: ComandoRegistrarOcorrencia): Promise<EstadoOcorrencia> {
    await this.d.autorizador.exigir(ator, Acao.OCORRENCIA_REGISTRAR, { tipo: "ocorrencia", id: "novo" });

    const agora = this.d.relogio.agora();
    const id = this.d.ids.gerar();
    const protocolo = await this.d.ocorrencias.proximoProtocolo(agora.getFullYear());

    // UC01 Exceção II — formato de arquivo validado antes de qualquer persistência.
    const evidencias = cmd.evidencias.map((ev) => {
      const tipoMime = validarFormatoEvidencia(ev.nomeArquivo);
      return {
        id: this.d.ids.gerar(),
        nomeArquivo: ev.nomeArquivo,
        tipoMime,
        tamanhoBytes: ev.tamanhoBytes,
        hashConteudo: this.d.hash.sha256(ev.conteudoBase64 ?? `${ev.nomeArquivo}:${ev.tamanhoBytes}`),
        anexadaEm: agora,
      };
    });

    const ocorrencia = Ocorrencia.registrar({
      id,
      protocolo,
      tipificacao: cmd.tipificacao,
      descricaoFato: cmd.descricaoFato,
      endereco: cmd.endereco,
      coordenada: cmd.coordenada,
      gravidade: cmd.gravidade,
      envolvidos: cmd.envolvidos.map((e) => ({ ...e, id: this.d.ids.gerar() })),
      evidencias,
      agenteId: ator.id,
      criadaEm: agora,
    });

    await this.d.ocorrencias.salvar(ocorrencia);
    await this.d.auditoria.registrar({
      atorId: ator.id, atorPapel: ator.papel, acao: Acao.OCORRENCIA_REGISTRAR,
      recursoTipo: "ocorrencia", recursoId: ocorrencia.id, resultado: "SUCESSO",
      detalhes: { protocolo, envolvidos: cmd.envolvidos.length, evidencias: evidencias.length },
    });
    this.d.eventos.publicar(eventoAlterada(ocorrencia, agora));
    return ocorrencia.paraEstado();
  }
}

export class CorrigirOcorrenciaUseCase implements CorrigirOcorrencia {
  constructor(private readonly d: DependenciasOcorrencia) {}

  async executar(ator: Ator, ocorrenciaId: string, novaDescricao: string): Promise<EstadoOcorrencia> {
    await this.d.autorizador.exigir(ator, Acao.OCORRENCIA_CORRIGIR, { tipo: "ocorrencia", id: ocorrenciaId });
    const atual = await this.d.ocorrencias.obterPorId(ocorrenciaId);
    if (!atual) throw new ErroNaoEncontrado("Ocorrência", ocorrenciaId);

    const agora = this.d.relogio.agora();
    const corrigida = atual.corrigirEReenviar(ator.id, novaDescricao, agora);
    await this.d.ocorrencias.salvar(corrigida);
    await this.d.auditoria.registrar({
      atorId: ator.id, atorPapel: ator.papel, acao: Acao.OCORRENCIA_CORRIGIR,
      recursoTipo: "ocorrencia", recursoId: ocorrenciaId, resultado: "SUCESSO",
      // RNF03: retificação auditada — guarda hash da versão anterior e da nova.
      detalhes: { hashAnterior: this.d.hash.sha256(atual.descricaoFato), hashNovo: this.d.hash.sha256(novaDescricao) },
    });
    this.d.eventos.publicar(eventoAlterada(corrigida, agora));
    return corrigida.paraEstado();
  }
}

export class ConsultarOcorrenciasUseCase implements ConsultarOcorrencias {
  constructor(private readonly d: DependenciasOcorrencia) {}

  async listar(ator: Ator, filtro?: { status?: StatusOcorrencia[] }): Promise<EstadoOcorrencia[]> {
    await this.d.autorizador.exigir(ator, Acao.OCORRENCIA_CONSULTAR, { tipo: "ocorrencia", id: "*" });
    // Agente vê apenas as próprias ocorrências; demais papéis veem todas.
    const escopo = ator.papel === "AGENTE" ? { agenteId: ator.id } : {};
    const lista = await this.d.ocorrencias.listar({ ...escopo, status: filtro?.status });
    // UC04 passo 2: ordenadas por gravidade (desc) e antiguidade (asc).
    return lista
      .map((o) => o.paraEstado())
      .sort((a, b) => b.gravidade - a.gravidade || a.criadaEm.getTime() - b.criadaEm.getTime());
  }

  async obter(ator: Ator, id: string): Promise<EstadoOcorrencia> {
    await this.d.autorizador.exigir(ator, Acao.OCORRENCIA_CONSULTAR, { tipo: "ocorrencia", id });
    const o = await this.d.ocorrencias.obterPorId(id);
    if (!o) throw new ErroNaoEncontrado("Ocorrência", id);
    if (ator.papel === "AGENTE" && o.agenteId !== ator.id) throw new ErroNaoEncontrado("Ocorrência", id);
    return o.paraEstado();
  }
}

/** UC04 — Validar Ocorrência. */
export class ValidarOcorrenciaUseCase implements ValidarOcorrencia {
  constructor(private readonly d: DependenciasOcorrencia) {}

  async executar(ator: Ator, ocorrenciaId: string, despachoAutoridade: string): Promise<EstadoOcorrencia> {
    // UC04 RN1 / Exceção I — tentativa por perfil não autorizado é negada e auditada.
    await this.d.autorizador.exigir(ator, Acao.OCORRENCIA_VALIDAR, { tipo: "ocorrencia", id: ocorrenciaId });
    const atual = await this.d.ocorrencias.obterPorId(ocorrenciaId);
    if (!atual) throw new ErroNaoEncontrado("Ocorrência", ocorrenciaId);

    const agora = this.d.relogio.agora();
    // UC04 RN2 — chave de integridade da narrativa.
    const hashNarrativa = this.d.hash.sha256(`${atual.id}|${atual.descricaoFato}`);
    const validada = atual.validar(ator.id, despachoAutoridade, hashNarrativa, agora);

    await this.d.ocorrencias.salvar(validada);
    await this.d.auditoria.registrar({
      atorId: ator.id, atorPapel: ator.papel, acao: Acao.OCORRENCIA_VALIDAR,
      recursoTipo: "ocorrencia", recursoId: ocorrenciaId, resultado: "SUCESSO",
      detalhes: { protocolo: validada.protocolo, hashIntegridade: hashNarrativa },
    });
    // UC04 passo 9 — libera para o painel tático (SSE).
    this.d.eventos.publicar(eventoAlterada(validada, agora));
    return validada.paraEstado();
  }
}

export class DevolverOcorrenciaUseCase implements DevolverOcorrenciaParaCorrecao {
  constructor(private readonly d: DependenciasOcorrencia) {}

  async executar(ator: Ator, ocorrenciaId: string, pendencias: string): Promise<EstadoOcorrencia> {
    await this.d.autorizador.exigir(ator, Acao.OCORRENCIA_DEVOLVER, { tipo: "ocorrencia", id: ocorrenciaId });
    const atual = await this.d.ocorrencias.obterPorId(ocorrenciaId);
    if (!atual) throw new ErroNaoEncontrado("Ocorrência", ocorrenciaId);

    const agora = this.d.relogio.agora();
    const devolvida = atual.devolverParaCorrecao(ator.id, pendencias, agora);
    await this.d.ocorrencias.salvar(devolvida);
    await this.d.auditoria.registrar({
      atorId: ator.id, atorPapel: ator.papel, acao: Acao.OCORRENCIA_DEVOLVER,
      recursoTipo: "ocorrencia", recursoId: ocorrenciaId, resultado: "SUCESSO",
      detalhes: { pendencias },
    });
    this.d.eventos.publicar(eventoAlterada(devolvida, agora));
    return devolvida.paraEstado();
  }
}
