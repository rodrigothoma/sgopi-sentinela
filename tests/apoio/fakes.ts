import type { PortaGeradorId, PortaHash, PortaRelogio, PublicadorEventos, Assinante } from "@/core/application/ports/outbound/Infraestrutura";
import type { EventoDominio } from "@/core/domain/shared/Evento";
import { AuditoriaHashChain } from "@/adapters/outbound/auditoria/AuditoriaHashChain";
import { Autorizador } from "@/core/application/seguranca/Autorizador";
import {
  RepositorioDespachosEmMemoria,
  RepositorioOcorrenciasEmMemoria,
  RepositorioViaturasEmMemoria,
} from "@/adapters/outbound/persistencia/memoria/RepositoriosEmMemoria";
import type { Ator } from "@/core/application/seguranca/Ator";
import type { ComandoRegistrarOcorrencia } from "@/core/application/ports/inbound/CasosDeUso";
import type { EstadoViatura } from "@/core/domain/viatura/Viatura";

/** Relógio controlável — essencial para testar a tolerância de 60 s do GPS. */
export class RelogioFixo implements PortaRelogio {
  constructor(public atual = new Date("2026-09-13T12:00:00Z")) {}
  agora(): Date { return new Date(this.atual); }
  avancar(ms: number): void { this.atual = new Date(this.atual.getTime() + ms); }
}

export class IdsSequenciais implements PortaGeradorId {
  private n = 0;
  gerar(): string { return `id-${++this.n}`; }
}

/** Hash determinístico e legível (não criptográfico) para os testes. */
export class HashFake implements PortaHash {
  sha256(c: string): string {
    let h = 0;
    for (const ch of c) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
    return `h${h.toString(16).padStart(8, "0")}`;
  }
}

export class EventosEmMemoria implements PublicadorEventos {
  publicados: EventoDominio[] = [];
  private assinantes = new Set<Assinante>();
  publicar(e: EventoDominio): void { this.publicados.push(e); this.assinantes.forEach((a) => a(e)); }
  assinar(a: Assinante): () => void { this.assinantes.add(a); return () => this.assinantes.delete(a); }
  tipos(): string[] { return this.publicados.map((e) => e.tipo); }
}

export const AGENTE: Ator = { id: "u-agente", nome: "Agente", papel: "AGENTE" };
export const OUTRO_AGENTE: Ator = { id: "u-agente-2", nome: "Agente 2", papel: "AGENTE" };
export const DELEGADO: Ator = { id: "u-delegado", nome: "Delegado", papel: "DELEGADO" };
export const OPERADOR: Ator = { id: "u-operador", nome: "Operador", papel: "OPERADOR_CENTRAL" };
export const SUPERVISOR: Ator = { id: "u-supervisor", nome: "Supervisor", papel: "SUPERVISOR" };

export function comandoOcorrenciaValido(extra: Partial<ComandoRegistrarOcorrencia> = {}): ComandoRegistrarOcorrencia {
  return {
    tipificacao: "Furto",
    descricaoFato: "Subtração de bicicleta estacionada em frente ao comércio, por volta das 14h.",
    gravidade: 2,
    endereco: { logradouro: "Rua dos Andradas", numero: "100", bairro: "Centro", cidade: "Alegrete", uf: "RS" },
    coordenada: { latitude: -29.7831, longitude: -55.7918 },
    envolvidos: [{ nome: "Maria da Silva", tipo: "VITIMA" }],
    evidencias: [],
    ...extra,
  };
}

export function viaturasDeTeste(): EstadoViatura[] {
  return [
    { id: "v1", prefixo: "VTR-1", placa: "AAA", equipe: "A", status: "DISPONIVEL" },
    { id: "v2", prefixo: "VTR-2", placa: "BBB", equipe: "B", status: "DISPONIVEL" },
    { id: "v3", prefixo: "VTR-3", placa: "CCC", equipe: "C", status: "DISPONIVEL" },
    { id: "v4", prefixo: "VTR-4", placa: "DDD", equipe: "D", status: "INDISPONIVEL" },
  ];
}

/** Monta um "mini-container" só com adaptadores em memória/fakes. */
export function montarAmbiente() {
  const relogio = new RelogioFixo();
  const ids = new IdsSequenciais();
  const hash = new HashFake();
  const eventos = new EventosEmMemoria();
  const auditoria = new AuditoriaHashChain(hash, relogio);
  const autorizador = new Autorizador(auditoria);
  const ocorrencias = new RepositorioOcorrenciasEmMemoria();
  const viaturas = new RepositorioViaturasEmMemoria(viaturasDeTeste());
  const despachos = new RepositorioDespachosEmMemoria();
  return { relogio, ids, hash, eventos, auditoria, autorizador, ocorrencias, viaturas, despachos };
}
