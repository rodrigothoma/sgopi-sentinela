import { Ocorrencia, type EstadoOcorrencia } from "@/core/domain/ocorrencia/Ocorrencia";
import { Viatura, type EstadoViatura } from "@/core/domain/viatura/Viatura";
import type { OrdemDespacho } from "@/core/domain/despacho/OrdemDespacho";
import type { Usuario } from "@/core/domain/usuario/Usuario";
import type {
  FiltroOcorrencias,
  RepositorioDespachos,
  RepositorioOcorrencias,
  RepositorioUsuarios,
  RepositorioViaturas,
} from "@/core/application/ports/outbound/Repositorios";

/**
 * Adaptadores de persistência em memória (MVP). Guardam *snapshots* (estado
 * serializável) e reidratam o agregado na leitura — exatamente o que um
 * adaptador Firestore/PostgreSQL faria, o que facilita a troca futura.
 */
export class RepositorioOcorrenciasEmMemoria implements RepositorioOcorrencias {
  private readonly dados = new Map<string, EstadoOcorrencia>();
  private readonly contadores = new Map<number, number>();

  async salvar(o: Ocorrencia): Promise<void> {
    this.dados.set(o.id, o.paraEstado());
  }

  async obterPorId(id: string): Promise<Ocorrencia | null> {
    const e = this.dados.get(id);
    return e ? Ocorrencia.reidratar(e) : null;
  }

  async listar(filtro?: FiltroOcorrencias): Promise<Ocorrencia[]> {
    return [...this.dados.values()]
      .filter((e) => !filtro?.status || filtro.status.length === 0 || filtro.status.includes(e.status))
      .filter((e) => !filtro?.agenteId || e.agenteId === filtro.agenteId)
      .map(Ocorrencia.reidratar);
  }

  async proximoProtocolo(ano: number): Promise<string> {
    const n = (this.contadores.get(ano) ?? 0) + 1;
    this.contadores.set(ano, n);
    return `BO-${ano}-${String(n).padStart(6, "0")}`;
  }
}

export class RepositorioViaturasEmMemoria implements RepositorioViaturas {
  private readonly dados = new Map<string, EstadoViatura>();

  constructor(iniciais: EstadoViatura[] = []) {
    iniciais.forEach((v) => this.dados.set(v.id, v));
  }
  async salvar(v: Viatura): Promise<void> {
    this.dados.set(v.id, v.paraEstado());
  }
  async obterPorId(id: string): Promise<Viatura | null> {
    const e = this.dados.get(id);
    return e ? Viatura.reidratar(e) : null;
  }
  async listar(): Promise<Viatura[]> {
    return [...this.dados.values()].map(Viatura.reidratar);
  }
}

export class RepositorioDespachosEmMemoria implements RepositorioDespachos {
  private readonly dados: OrdemDespacho[] = [];
  async salvar(o: OrdemDespacho): Promise<void> {
    this.dados.push(Object.freeze({ ...o })); // ordens são imutáveis (RNF03)
  }
  async listar(): Promise<OrdemDespacho[]> {
    return [...this.dados];
  }
  async listarPorOcorrencia(ocorrenciaId: string): Promise<OrdemDespacho[]> {
    return this.dados.filter((d) => d.ocorrenciaId === ocorrenciaId);
  }
}

export class RepositorioUsuariosEmMemoria implements RepositorioUsuarios {
  private readonly porMatricula = new Map<string, Usuario>();
  private readonly porId = new Map<string, Usuario>();

  constructor(usuarios: Usuario[]) {
    usuarios.forEach((u) => {
      this.porMatricula.set(u.matricula, u);
      this.porId.set(u.id, u);
    });
  }
  async obterPorMatricula(m: string): Promise<Usuario | null> {
    return this.porMatricula.get(m) ?? null;
  }
  async obterPorId(id: string): Promise<Usuario | null> {
    return this.porId.get(id) ?? null;
  }
}
