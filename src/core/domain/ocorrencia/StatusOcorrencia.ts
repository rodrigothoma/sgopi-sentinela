import { ErroTransicaoInvalida } from "../shared/DomainError";

/**
 * Máquina de estados da ocorrência (Seção 3.2 + UC02/UC04).
 *
 * Observação de análise: a documentação usa nomes distintos para o mesmo
 * estado em seções diferentes ("Rejeitada" vs "Em Correção"; "Em Despacho" vs
 * "Em Atendimento"). Adotou-se a nomenclatura dos casos de uso (UC02/UC04),
 * que é mais específica. Ver docs/mvp/03-problemas-encontrados.md.
 */
export const StatusOcorrencia = {
  AGUARDANDO_REVISAO: "AGUARDANDO_REVISAO",
  EM_CORRECAO: "EM_CORRECAO",
  VALIDADA: "VALIDADA",
  EM_ATENDIMENTO: "EM_ATENDIMENTO",
  CONCLUIDA: "CONCLUIDA",
} as const;

export type StatusOcorrencia = (typeof StatusOcorrencia)[keyof typeof StatusOcorrencia];

const TRANSICOES: Record<StatusOcorrencia, readonly StatusOcorrencia[]> = {
  AGUARDANDO_REVISAO: ["VALIDADA", "EM_CORRECAO"],
  EM_CORRECAO: ["AGUARDANDO_REVISAO"],
  VALIDADA: ["EM_ATENDIMENTO"],
  EM_ATENDIMENTO: ["CONCLUIDA"],
  CONCLUIDA: [],
};

export function assegurarTransicao(de: StatusOcorrencia, para: StatusOcorrencia): void {
  if (!TRANSICOES[de].includes(para)) {
    throw new ErroTransicaoInvalida(de, para);
  }
}

export const ROTULO_STATUS: Record<StatusOcorrencia, string> = {
  AGUARDANDO_REVISAO: "Aguardando Revisão",
  EM_CORRECAO: "Em Correção",
  VALIDADA: "Validada",
  EM_ATENDIMENTO: "Em Atendimento",
  CONCLUIDA: "Concluída",
};
