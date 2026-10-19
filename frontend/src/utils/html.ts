const ENTIDADES: Record<string, string> = {
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  "'": '&#39;',
};

/**
 * Escapa texto para interpolação em HTML montado como string (popups, tooltips e `divIcon` do
 * Leaflet interpretam strings como HTML). Todo dado vindo da API — em especial `natureza`, aceita
 * no registro público anônimo — deve passar por aqui antes de virar markup.
 */
export function escaparHtml(valor: unknown): string {
  return String(valor ?? '').replace(/[&<>"']/g, (c) => ENTIDADES[c]);
}
