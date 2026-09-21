// Contratos espelhados do OpenAPI do backend (RNF12). Manter sincronizado por revisão.
export type Papel = 'AGENTE' | 'DELEGADO' | 'OPERADOR_CENTRAL' | 'SUPERVISOR' | 'PERITO' | 'ESCRIVAO';
export type TipoEnvolvido = 'VITIMA' | 'TESTEMUNHA' | 'SUSPEITO' | 'COMUNICANTE';
export type StatusOcorrencia = 'AGUARDANDO_REVISAO' | 'EM_CORRECAO' | 'REJEITADA' | 'VALIDADA' | 'EM_ATENDIMENTO' | 'ENCERRADA';
export type SituacaoViatura = 'DISPONIVEL' | 'EM_DESLOCAMENTO' | 'OPERANDO' | 'INDISPONIVEL';
export type Sinal = 'OK' | 'SEM_SINAL' | 'SEM_POSICAO';

export interface Usuario { id: string; nome: string; login: string; papel: Papel }
export interface LoginResponse { access_token: string; token_type: string; expira_em: string; usuario: Usuario }

export interface EnvolvidoDTO { nome: string; tipo: TipoEnvolvido; documento?: string; email?: string; telefone?: string }
export interface TipificacaoDTO { artigo: string; descricao: string }
export interface Evidencia {
  id: string; nome_original: string; formato: string; tamanho: number; hash_sha256: string; enviada_em: string;
}
export type EstadoIntegridadeEvidencia = 'INTEGRA' | 'DIVERGENTE';
export interface IntegridadeEvidencia { evidencia_id: string; estado: EstadoIntegridadeEvidencia }

export interface RegistrarOcorrenciaRequest {
  natureza: string; descricao: string; localizacao: string;
  latitude: number; longitude: number; data_hora_fato: string;
  tipificacoes: TipificacaoDTO[]; envolvidos: EnvolvidoDTO[];
}
export interface CorrigirOcorrenciaRequest extends Partial<RegistrarOcorrenciaRequest> {}

export interface OcorrenciaCriada { ocorrencia_id: string; numero_protocolo: string; status: StatusOcorrencia; criada_em: string }

export interface OcorrenciaResumo {
  ocorrencia_id: string; numero_protocolo: string; natureza: string; localizacao: string;
  latitude: number; longitude: number; status: StatusOcorrencia; data_hora_fato: string;
  criada_em: string; atualizada_em: string; agente_policial_id: string; versao: number;
}
export interface EnvolvidoDetalhe {
  id: string;
  nome: string;
  tipo: TipoEnvolvido;
  documento: string | null;
  email?: string | null;
  telefone?: string | null;
}
export interface HistoricoStatus { de: string | null; para: StatusOcorrencia; em: string; por_id: string; justificativa: string | null }
export interface OcorrenciaDetalhe extends OcorrenciaResumo {
  descricao: string; validada_por_id: string | null; justificativa_revisao: string | null; desfecho: string | null;
  hash_narrativa: string | null; narrativa_integra: boolean | null; chave_autenticidade: string | null;
  envolvidos: EnvolvidoDetalhe[]; tipificacoes: TipificacaoDTO[]; evidencias: Evidencia[]; historico_status: HistoricoStatus[];
}

/** RF08: espelho público de conferência — sem dados pessoais. */
export type SituacaoDocumento = 'VALIDO' | 'ADULTERADO';
export interface DocumentoAutenticado {
  numero_protocolo: string; situacao: SituacaoDocumento; emitido_em: string; consultado_em: string;
  natureza: string; data_hora_fato: string; status_ocorrencia: StatusOcorrencia; hash_integridade: string;
  tipificacoes: TipificacaoDTO[]; envolvidos_por_tipo: Partial<Record<TipoEnvolvido, number>>; quantidade_evidencias: number;
}
export interface Pagina<T> { itens: T[]; total: number; limit: number; offset: number }

export interface Viatura {
  id: string; prefixo: string; placa: string; situacao: SituacaoViatura;
  latitude: number | null; longitude: number | null; posicao_registrada_em: string | null; sinal: Sinal; versao: number;
}
export interface ViaturaSugerida { viatura: Viatura; distancia_km: number }
export interface Sugestoes { ocorrencia_id: string; sugestoes: ViaturaSugerida[]; sem_elegiveis: boolean; disponiveis_sem_posicao: Viatura[] }
export interface OrdemDespacho {
  id: string; numero: string; ocorrencia_id: string; viatura_id: string; operador_id: string;
  criada_em: string; observacoes: string | null; ativa: boolean; encerrada_em: string | null;
}
export interface StatusSimulador { ligado: boolean; intervalo_segundos: number; raio_metros: number; ticks: number; posicoes_emitidas: number }

export interface EventoTempoReal { tipo: string; ocorrido_em: string; dados: Record<string, unknown> }

export interface RegistroAuditoria {
  id: string;
  quando: string;
  quem: string | null;
  operacao: string;
  entidade: string;
  entidade_id: string | null;
  dados_antes: Record<string, unknown> | null;
  dados_depois: Record<string, unknown> | null;
  ip: string | null;
  autor_nome?: string | null;
  autor_papel?: Papel | null;
  identificador_amigavel?: string | null;
}

export interface FiltroAuditoria {
  entidade?: string;
  entidade_id?: string;
  operacao?: string;
  quem?: string;
  limit?: number;
}

export interface ErroApi { detail: string; code: string; request_id: string | null; extra?: Record<string, unknown> }
