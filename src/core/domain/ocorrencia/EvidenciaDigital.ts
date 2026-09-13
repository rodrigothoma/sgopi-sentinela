import { ErroValidacao } from "../shared/DomainError";

/**
 * O MVP não faz upload de binários (Seção 3.2 — limites). Armazena-se apenas
 * metadados e o hash do conteúdo, o que já garante o vínculo permanente e a
 * verificação de integridade (RNF03). O binário em si fica para um adaptador
 * de armazenamento futuro.
 */
export interface EvidenciaDigital {
  readonly id: string;
  readonly nomeArquivo: string;
  readonly tipoMime: string;
  readonly tamanhoBytes: number;
  readonly hashConteudo: string;
  readonly anexadaEm: Date;
}

/** Formatos aceitos conforme UC01 — Cenário de Exceção II. */
export const FORMATOS_EVIDENCIA_ACEITOS: ReadonlyMap<string, string> = new Map([
  ["pdf", "application/pdf"],
  ["jpg", "image/jpeg"],
  ["jpeg", "image/jpeg"],
  ["png", "image/png"],
]);

export function validarFormatoEvidencia(nomeArquivo: string): string {
  const extensao = nomeArquivo.toLowerCase().split(".").pop() ?? "";
  const mime = FORMATOS_EVIDENCIA_ACEITOS.get(extensao);
  if (!mime) {
    throw new ErroValidacao(`Formato de arquivo não suportado: .${extensao}`, {
      nomeArquivo,
      aceitos: [...FORMATOS_EVIDENCIA_ACEITOS.keys()],
    });
  }
  return mime;
}
