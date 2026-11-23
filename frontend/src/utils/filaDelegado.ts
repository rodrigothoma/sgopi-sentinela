import type { OcorrenciaResumo, OrigemOcorrencia, PrioridadeOcorrencia } from '../types/api';

const PESO_PRIORIDADE: Record<PrioridadeOcorrencia, number> = { URGENTE: 4, ALTA: 3, MEDIA: 2, BAIXA: 1 };

/** Ordem da fila: mais graves primeiro; dentro da mesma gravidade, a mais antiga. */
export function inserirOrdenado(itens: OcorrenciaResumo[], nova: OcorrenciaResumo): OcorrenciaResumo[] {
  return [...itens, nova].sort(
    (a, b) =>
      (PESO_PRIORIDADE[b.prioridade ?? 'MEDIA'] - PESO_PRIORIDADE[a.prioridade ?? 'MEDIA']) ||
      a.criada_em.localeCompare(b.criada_em),
  );
}

/** Chegada em tempo real sem refetch total: a notificação da fila reconstrói o resumo. */
export function resumoDaNotificacao(d: Record<string, unknown>): OcorrenciaResumo {
  const criadaEm = String(d.criada_em ?? new Date().toISOString());
  return {
    ocorrencia_id: String(d.ocorrencia_id ?? ''),
    numero_protocolo: String(d.numero_protocolo ?? ''),
    natureza: String(d.natureza ?? ''),
    localizacao: String(d.localizacao ?? ''),
    latitude: Number(d.latitude ?? 0),
    longitude: Number(d.longitude ?? 0),
    status: 'AGUARDANDO_REVISAO',
    data_hora_fato: criadaEm,
    criada_em: criadaEm,
    atualizada_em: criadaEm,
    agente_policial_id: String(d.agente_policial_id ?? ''),
    versao: 0,
    origem: (d.origem as OrigemOcorrencia) ?? 'POLICIAL',
    prioridade: (d.prioridade as PrioridadeOcorrencia) ?? 'MEDIA',
  };
}
