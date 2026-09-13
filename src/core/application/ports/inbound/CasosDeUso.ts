import type { EstadoOcorrencia, Endereco, Gravidade } from "@/core/domain/ocorrencia/Ocorrencia";
import type { TipoEnvolvido } from "@/core/domain/ocorrencia/Envolvido";
import type { StatusOcorrencia } from "@/core/domain/ocorrencia/StatusOcorrencia";
import type { EstadoViatura } from "@/core/domain/viatura/Viatura";
import type { OrdemDespacho } from "@/core/domain/despacho/OrdemDespacho";
import type { RegistroAuditoria } from "@/core/domain/auditoria/RegistroAuditoria";
import type { Coordenada } from "@/core/domain/shared/Coordenada";
import type { Ator } from "@/core/application/seguranca/Ator";

/**
 * Portas de entrada (inbound). Os adaptadores (HTTP, páginas React no
 * servidor, simulador GPS) dependem apenas destes contratos.
 */

// ----- UC01 -----
export interface ComandoRegistrarOcorrencia {
  readonly tipificacao: string;
  readonly descricaoFato: string;
  readonly endereco: Endereco;
  readonly coordenada?: Coordenada;
  readonly gravidade: Gravidade;
  readonly envolvidos: readonly {
    nome: string;
    tipo: TipoEnvolvido;
    documento?: string;
    dataNascimento?: string;
    observacoes?: string;
  }[];
  readonly evidencias: readonly { nomeArquivo: string; tamanhoBytes: number; conteudoBase64?: string }[];
}
export interface RegistrarOcorrencia {
  executar(ator: Ator, comando: ComandoRegistrarOcorrencia): Promise<EstadoOcorrencia>;
}

export interface CorrigirOcorrencia {
  executar(ator: Ator, ocorrenciaId: string, novaDescricao: string): Promise<EstadoOcorrencia>;
}

export interface ConsultarOcorrencias {
  listar(ator: Ator, filtro?: { status?: StatusOcorrencia[] }): Promise<EstadoOcorrencia[]>;
  obter(ator: Ator, id: string): Promise<EstadoOcorrencia>;
}

// ----- UC04 -----
export interface ValidarOcorrencia {
  executar(ator: Ator, ocorrenciaId: string, despachoAutoridade: string): Promise<EstadoOcorrencia>;
}
export interface DevolverOcorrenciaParaCorrecao {
  executar(ator: Ator, ocorrenciaId: string, pendencias: string): Promise<EstadoOcorrencia>;
}

// ----- UC02 -----
export interface ConsultarViaturas {
  listar(ator: Ator): Promise<ViaturaComSinal[]>;
}
export interface ViaturaComSinal extends EstadoViatura {
  readonly sinalGpsValido: boolean;
}

export interface AtualizarTelemetriaViatura {
  executar(ator: Ator, viaturaId: string, coordenada: Coordenada, recebidaEm?: Date): Promise<void>;
}

export interface SugestaoViatura {
  readonly viatura: ViaturaComSinal;
  readonly distanciaKm: number | null;
}
export interface ResultadoSugestao {
  readonly ocorrenciaId: string;
  readonly coordenadaOcorrencia?: Coordenada;
  /** true quando todas as viaturas disponíveis estão com GPS inválido (RNF04). */
  readonly despachoAutomaticoBloqueado: boolean;
  readonly sugestoes: readonly SugestaoViatura[];
}
export interface SugerirViaturasProximas {
  executar(ator: Ator, ocorrenciaId: string, limite?: number): Promise<ResultadoSugestao>;
}

export interface ComandoDespachar {
  readonly ocorrenciaId: string;
  readonly viaturaId: string;
  /** Obrigatório quando a viatura está sem GPS válido (despacho manual). */
  readonly posicaoInformada?: Coordenada;
  readonly observacao?: string;
}
export interface DespacharViatura {
  executar(ator: Ator, comando: ComandoDespachar): Promise<OrdemDespacho>;
}
export interface ConsultarDespachos {
  listar(ator: Ator): Promise<OrdemDespacho[]>;
}

// ----- Segurança / Auditoria -----
export interface AutenticarUsuario {
  executar(matricula: string, senha: string): Promise<Ator>;
}
export interface ConsultarAuditoria {
  listar(ator: Ator, limite?: number): Promise<{ registros: RegistroAuditoria[]; integra: boolean }>;
}
