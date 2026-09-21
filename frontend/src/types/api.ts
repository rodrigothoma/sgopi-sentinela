// Contratos espelhados do OpenAPI do backend (RNF12). Manter sincronizado por revisão.
export type Papel = 'AGENTE' | 'DELEGADO' | 'OPERADOR_CENTRAL' | 'SUPERVISOR' | 'PERITO' | 'ESCRIVAO';
export type TipoEnvolvido = 'VITIMA' | 'TESTEMUNHA' | 'SUSPEITO' | 'COMUNICANTE';
export type StatusOcorrencia = 'AGUARDANDO_REVISAO' | 'EM_CORRECAO' | 'REJEITADA' | 'VALIDADA' | 'EM_ATENDIMENTO' | 'ENCERRADA' | 'ARQUIVADA' | 'EXCLUIDA';
/** Atos administrativos do Delegado (RF20): não permitidos em EM_ATENDIMENTO; EXCLUIDA é terminal. */
export const STATUS_ARQUIVAVEIS: readonly StatusOcorrencia[] = ['AGUARDANDO_REVISAO', 'EM_CORRECAO', 'REJEITADA', 'VALIDADA', 'ENCERRADA'];
export const STATUS_EXCLUIVEIS: readonly StatusOcorrencia[] = [...STATUS_ARQUIVAVEIS, 'ARQUIVADA'];
/** RF03 / UC03: apreensões só pelo Agente autor com a ocorrência registrada ou em andamento. */
export const STATUS_ACEITAM_APREENSAO: readonly StatusOcorrencia[] = ['AGUARDANDO_REVISAO', 'EM_CORRECAO', 'VALIDADA', 'EM_ATENDIMENTO'];
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

// --- RF03: itens apreendidos e cadeia de custódia ---
export type TipoItemApreendido = 'ARMA_DE_FOGO' | 'ARMA_BRANCA' | 'ENTORPECENTE' | 'VEICULO' | 'VALOR' | 'OBJETO';
export type UnidadeMedida = 'UNIDADE' | 'GRAMA' | 'QUILOGRAMA' | 'MILILITRO' | 'LITRO';
export type EstadoConservacao = 'NOVO' | 'BOM' | 'REGULAR' | 'DANIFICADO' | 'INSERVIVEL';
export const TIPOS_ITEM_APREENDIDO: readonly TipoItemApreendido[] = ['ARMA_DE_FOGO', 'ARMA_BRANCA', 'ENTORPECENTE', 'VEICULO', 'VALOR', 'OBJETO'];
export const UNIDADES_MEDIDA: readonly UnidadeMedida[] = ['UNIDADE', 'GRAMA', 'QUILOGRAMA', 'MILILITRO', 'LITRO'];
export const ESTADOS_CONSERVACAO: readonly EstadoConservacao[] = ['NOVO', 'BOM', 'REGULAR', 'DANIFICADO', 'INSERVIVEL'];

/** Entrada de cadastro (registro concomitante ou pela aba de apreensões). */
export interface ItemApreendidoDTO {
  tipo: TipoItemApreendido; descricao: string; quantidade: number; unidade: UnidadeMedida;
  estado_conservacao: EstadoConservacao; numero_lacre: string; localizacao_deposito: string;
  numero_serie?: string | null; marca?: string | null; calibre?: string | null;
}
export interface MovimentacaoCustodia { em: string; por_id: string; origem: string | null; destino: string; observacao: string | null }
export interface ItemApreendido extends Required<Omit<ItemApreendidoDTO, 'numero_serie' | 'marca' | 'calibre'>> {
  id: string; numero_serie: string | null; marca: string | null; calibre: string | null;
  localizacao_atual: string; registrado_em: string; registrado_por_id: string; movimentacoes: MovimentacaoCustodia[];
}
export interface MovimentarCustodiaRequest { destino: string; observacao?: string | null }
/** Auto de Apreensão: identificador único derivado do protocolo + hash SHA-256 do conteúdo (RNF03). */
export interface AutoApreensao {
  numero: string; ocorrencia_id: string; numero_protocolo: string; natureza: string; localizacao: string;
  data_hora_fato: string; status: StatusOcorrencia; agente_policial_id: string;
  emitido_em: string; emitido_por_id: string; hash_sha256: string; itens: ItemApreendido[];
}

export interface RegistrarOcorrenciaRequest {
  natureza: string; descricao: string; localizacao: string;
  latitude: number; longitude: number; data_hora_fato: string;
  tipificacoes: TipificacaoDTO[]; envolvidos: EnvolvidoDTO[];
  /** RF03 — opcional: apreensão concomitante ao registro (mesma transação). */
  itens_apreendidos?: ItemApreendidoDTO[];
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
  hash_narrativa: string | null; narrativa_integra: boolean | null;
  /** RF08: chave pública do documento emitido (só após validação pelo Delegado). */
  chave_autenticidade: string | null;
  arquivada_por_id: string | null; motivo_arquivamento: string | null;
  excluida_por_id: string | null; motivo_exclusao: string | null;
  envolvidos: EnvolvidoDetalhe[]; tipificacoes: TipificacaoDTO[]; evidencias: Evidencia[]; historico_status: HistoricoStatus[];
  itens_apreendidos: ItemApreendido[];
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
export interface StatusSimulador { ligado: boolean; intervalo_segundos: number; raio_metros: number; velocidade_kmh?: number; ticks: number; posicoes_emitidas: number }

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

/** RF08 / UC08 — resultado da conferência pública do documento. */
export type SituacaoDocumento = 'AUTENTICO' | 'ADULTERADO' | 'INDISPONIVEL';
export interface DocumentoAutenticado {
  numero_protocolo: string;
  situacao: SituacaoDocumento;
  chave_autenticidade: string;
  chave_formatada: string;
  emitido_em: string;
  consultado_em: string;
  natureza: string;
  data_hora_fato: string;
  status_ocorrencia: StatusOcorrencia;
  hash_integridade: string;
  tipificacoes: TipificacaoDTO[];
  envolvidos_por_tipo: Record<string, number>;
  quantidade_evidencias: number;
}
