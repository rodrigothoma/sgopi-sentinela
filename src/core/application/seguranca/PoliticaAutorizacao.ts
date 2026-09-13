import { Papel } from "@/core/domain/usuario/Papel";

/**
 * RNF02 — matriz RBAC. Centralizada para que a checagem ocorra na porta de
 * entrada (adaptadores) E dentro dos casos de uso (defesa em profundidade).
 */
export const Acao = {
  OCORRENCIA_REGISTRAR: "ocorrencia.registrar",
  OCORRENCIA_CORRIGIR: "ocorrencia.corrigir",
  OCORRENCIA_CONSULTAR: "ocorrencia.consultar",
  OCORRENCIA_VALIDAR: "ocorrencia.validar",
  OCORRENCIA_DEVOLVER: "ocorrencia.devolver",
  VIATURA_CONSULTAR: "viatura.consultar",
  VIATURA_TELEMETRIA: "viatura.telemetria",
  DESPACHO_SUGERIR: "despacho.sugerir",
  DESPACHO_EMITIR: "despacho.emitir",
  AUDITORIA_CONSULTAR: "auditoria.consultar",
} as const;
export type Acao = (typeof Acao)[keyof typeof Acao];

const { AGENTE, DELEGADO, OPERADOR_CENTRAL, SUPERVISOR, PERITO } = Papel;

export const MATRIZ_PERMISSOES: Record<Acao, readonly Papel[]> = {
  [Acao.OCORRENCIA_REGISTRAR]: [AGENTE],
  [Acao.OCORRENCIA_CORRIGIR]: [AGENTE],
  [Acao.OCORRENCIA_CONSULTAR]: [AGENTE, DELEGADO, OPERADOR_CENTRAL, SUPERVISOR, PERITO],
  [Acao.OCORRENCIA_VALIDAR]: [DELEGADO],
  [Acao.OCORRENCIA_DEVOLVER]: [DELEGADO],
  [Acao.VIATURA_CONSULTAR]: [OPERADOR_CENTRAL, SUPERVISOR, DELEGADO],
  [Acao.VIATURA_TELEMETRIA]: [SUPERVISOR], // ATOR_SISTEMA usa este papel
  [Acao.DESPACHO_SUGERIR]: [OPERADOR_CENTRAL, SUPERVISOR],
  [Acao.DESPACHO_EMITIR]: [OPERADOR_CENTRAL],
  [Acao.AUDITORIA_CONSULTAR]: [SUPERVISOR, DELEGADO],
};

export function papelPodeExecutar(papel: Papel, acao: Acao): boolean {
  return MATRIZ_PERMISSOES[acao].includes(papel);
}
