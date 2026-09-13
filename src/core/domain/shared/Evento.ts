/**
 * Evento de domínio. Publicado pelos casos de uso através da porta de saída
 * `PublicadorEventos`; consumido por adaptadores (SSE, auditoria, etc.).
 */
export interface EventoDominio<TTipo extends string = string, TPayload = unknown> {
  readonly tipo: TTipo;
  readonly ocorridoEm: Date;
  readonly payload: TPayload;
}
