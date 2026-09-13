/**
 * Erros de domínio são a única forma de o núcleo sinalizar violação de regra
 * de negócio. Adaptadores de entrada traduzem cada `codigo` para HTTP/UI.
 */
export type CodigoErroDominio =
  | "VALIDACAO"
  | "NAO_ENCONTRADO"
  | "TRANSICAO_INVALIDA"
  | "NAO_AUTORIZADO"
  | "CONFLITO"
  | "PRE_CONDICAO";

/**
 * Marca global para reconhecer erros de domínio SEM depender de `instanceof`.
 * Bundlers (Turbopack/webpack) podem duplicar um módulo em chunks distintos,
 * fazendo `instanceof` falhar entre eles; `Symbol.for` é único por runtime.
 */
export const MARCA_ERRO_DOMINIO = Symbol.for("sgopi.DomainError");

export class DomainError extends Error {
  readonly [MARCA_ERRO_DOMINIO] = true;

  constructor(
    public readonly codigo: CodigoErroDominio,
    message: string,
    public readonly detalhes?: Record<string, unknown>,
  ) {
    super(message);
    this.name = "DomainError";
  }
}

export function ehErroDominio(erro: unknown): erro is DomainError {
  return typeof erro === "object" && erro !== null && (erro as Record<symbol, unknown>)[MARCA_ERRO_DOMINIO] === true;
}

export class ErroValidacao extends DomainError {
  constructor(message: string, detalhes?: Record<string, unknown>) {
    super("VALIDACAO", message, detalhes);
    this.name = "ErroValidacao";
  }
}

export class ErroNaoEncontrado extends DomainError {
  constructor(recurso: string, id: string) {
    super("NAO_ENCONTRADO", `${recurso} '${id}' não encontrado(a).`, { recurso, id });
    this.name = "ErroNaoEncontrado";
  }
}

export class ErroTransicaoInvalida extends DomainError {
  constructor(de: string, para: string) {
    super("TRANSICAO_INVALIDA", `Transição de status inválida: ${de} → ${para}.`, { de, para });
    this.name = "ErroTransicaoInvalida";
  }
}

export class ErroNaoAutorizado extends DomainError {
  constructor(acao: string, papel: string) {
    super("NAO_AUTORIZADO", `Papel '${papel}' não possui permissão para '${acao}'.`, { acao, papel });
    this.name = "ErroNaoAutorizado";
  }
}

export class ErroPreCondicao extends DomainError {
  constructor(message: string, detalhes?: Record<string, unknown>) {
    super("PRE_CONDICAO", message, detalhes);
    this.name = "ErroPreCondicao";
  }
}
