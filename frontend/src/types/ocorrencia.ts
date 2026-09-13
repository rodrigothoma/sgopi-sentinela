export type TipoEnvolvido = 'VITIMA' | 'TESTEMUNHA' | 'SUSPEITO';

export interface EnvolvidoDTO {
  nome: string;
  tipo: TipoEnvolvido;
  documento?: string;
}

export interface TipificacaoDTO {
  artigo: string;
  descricao: string;
}

export interface RegistrarOcorrenciaRequest {
  agente_policial_id: string;
  natureza: string;
  descricao: string;
  localizacao: string;
  tipificacoes: TipificacaoDTO[];
  envolvidos: EnvolvidoDTO[];
}

export interface OcorrenciaResponse {
  ocorrencia_id: string;
  numero_protocolo: string;
  status: string;
  criada_em: string;
}
