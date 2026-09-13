import type { Ocorrencia } from "@/core/domain/ocorrencia/Ocorrencia";
import type { StatusOcorrencia } from "@/core/domain/ocorrencia/StatusOcorrencia";
import type { Viatura } from "@/core/domain/viatura/Viatura";
import type { OrdemDespacho } from "@/core/domain/despacho/OrdemDespacho";
import type { Usuario } from "@/core/domain/usuario/Usuario";

export interface FiltroOcorrencias {
  readonly status?: readonly StatusOcorrencia[];
  readonly agenteId?: string;
}

export interface RepositorioOcorrencias {
  salvar(ocorrencia: Ocorrencia): Promise<void>;
  obterPorId(id: string): Promise<Ocorrencia | null>;
  listar(filtro?: FiltroOcorrencias): Promise<Ocorrencia[]>;
  /** UC01 passo 9 — número de protocolo único. */
  proximoProtocolo(ano: number): Promise<string>;
}

export interface RepositorioViaturas {
  salvar(viatura: Viatura): Promise<void>;
  obterPorId(id: string): Promise<Viatura | null>;
  listar(): Promise<Viatura[]>;
}

export interface RepositorioDespachos {
  salvar(ordem: OrdemDespacho): Promise<void>;
  listar(): Promise<OrdemDespacho[]>;
  listarPorOcorrencia(ocorrenciaId: string): Promise<OrdemDespacho[]>;
}

export interface RepositorioUsuarios {
  obterPorMatricula(matricula: string): Promise<Usuario | null>;
  obterPorId(id: string): Promise<Usuario | null>;
}
