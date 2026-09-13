import { Autorizador } from "@/core/application/seguranca/Autorizador";
import {
  ConsultarOcorrenciasUseCase,
  CorrigirOcorrenciaUseCase,
  DevolverOcorrenciaUseCase,
  RegistrarOcorrenciaUseCase,
  ValidarOcorrenciaUseCase,
  type DependenciasOcorrencia,
} from "@/core/application/usecases/OcorrenciaUseCases";
import {
  AtualizarTelemetriaUseCase,
  ConsultarDespachosUseCase,
  ConsultarViaturasUseCase,
  DespacharViaturaUseCase,
  SugerirViaturasProximasUseCase,
  type DependenciasDespacho,
} from "@/core/application/usecases/DespachoUseCases";
import { AutenticarUsuarioUseCase, ConsultarAuditoriaUseCase } from "@/core/application/usecases/SegurancaUseCases";
import { RelogioSistema } from "@/adapters/outbound/infra/RelogioSistema";
import { GeradorIdCrypto } from "@/adapters/outbound/infra/GeradorIdCrypto";
import { HashNodeCrypto } from "@/adapters/outbound/seguranca/HashNodeCrypto";
import { BarramentoEventosEmProcesso } from "@/adapters/outbound/eventos/BarramentoEventosEmProcesso";
import { AuditoriaHashChain } from "@/adapters/outbound/auditoria/AuditoriaHashChain";
import {
  RepositorioDespachosEmMemoria,
  RepositorioOcorrenciasEmMemoria,
  RepositorioUsuariosEmMemoria,
  RepositorioViaturasEmMemoria,
} from "@/adapters/outbound/persistencia/memoria/RepositoriosEmMemoria";
import { SimuladorGps } from "@/adapters/inbound/simulador-gps/SimuladorGps";
import { CENTRO_ALEGRETE, usuariosSeed, viaturasSeed } from "./seed";

/**
 * Composition root: o ÚNICO lugar que conhece adaptadores concretos e portas
 * ao mesmo tempo. Trocar Firestore por PostgreSQL, ou SSE por WebSocket,
 * altera apenas este arquivo (RNF05).
 */
export interface Container {
  readonly relogio: RelogioSistema;
  readonly hash: HashNodeCrypto;
  readonly eventos: BarramentoEventosEmProcesso;
  readonly auditoria: AuditoriaHashChain;
  readonly usuarios: RepositorioUsuariosEmMemoria;
  readonly casosDeUso: {
    readonly registrarOcorrencia: RegistrarOcorrenciaUseCase;
    readonly corrigirOcorrencia: CorrigirOcorrenciaUseCase;
    readonly consultarOcorrencias: ConsultarOcorrenciasUseCase;
    readonly validarOcorrencia: ValidarOcorrenciaUseCase;
    readonly devolverOcorrencia: DevolverOcorrenciaUseCase;
    readonly consultarViaturas: ConsultarViaturasUseCase;
    readonly atualizarTelemetria: AtualizarTelemetriaUseCase;
    readonly sugerirViaturas: SugerirViaturasProximasUseCase;
    readonly despacharViatura: DespacharViaturaUseCase;
    readonly consultarDespachos: ConsultarDespachosUseCase;
    readonly autenticarUsuario: AutenticarUsuarioUseCase;
    readonly consultarAuditoria: ConsultarAuditoriaUseCase;
  };
  readonly simuladorGps: SimuladorGps;
}

function montarContainer(): Container {
  const relogio = new RelogioSistema();
  const ids = new GeradorIdCrypto();
  const hash = new HashNodeCrypto();
  const eventos = new BarramentoEventosEmProcesso();
  const auditoria = new AuditoriaHashChain(hash, relogio);
  const autorizador = new Autorizador(auditoria);

  const ocorrencias = new RepositorioOcorrenciasEmMemoria();
  const viaturas = new RepositorioViaturasEmMemoria(viaturasSeed());
  const despachos = new RepositorioDespachosEmMemoria();
  const usuarios = new RepositorioUsuariosEmMemoria(usuariosSeed(hash));

  const depsOcorrencia: DependenciasOcorrencia = { ocorrencias, auditoria, relogio, ids, hash, eventos, autorizador };
  const depsDespacho: DependenciasDespacho = { ocorrencias, viaturas, despachos, auditoria, relogio, ids, eventos, autorizador };

  const consultarViaturas = new ConsultarViaturasUseCase(depsDespacho);
  const atualizarTelemetria = new AtualizarTelemetriaUseCase(depsDespacho);

  const simuladorGps = new SimuladorGps(atualizarTelemetria, consultarViaturas, {
    centro: CENTRO_ALEGRETE,
    intervaloMs: Number(process.env.GPS_SIMULADOR_INTERVALO_MS ?? 2000),
    viaturasComFalhaIntermitente: ["vtr-05"],
  });

  return {
    relogio, hash, eventos, auditoria, usuarios,
    casosDeUso: {
      registrarOcorrencia: new RegistrarOcorrenciaUseCase(depsOcorrencia),
      corrigirOcorrencia: new CorrigirOcorrenciaUseCase(depsOcorrencia),
      consultarOcorrencias: new ConsultarOcorrenciasUseCase(depsOcorrencia),
      validarOcorrencia: new ValidarOcorrenciaUseCase(depsOcorrencia),
      devolverOcorrencia: new DevolverOcorrenciaUseCase(depsOcorrencia),
      consultarViaturas,
      atualizarTelemetria,
      sugerirViaturas: new SugerirViaturasProximasUseCase(depsDespacho),
      despacharViatura: new DespacharViaturaUseCase(depsDespacho),
      consultarDespachos: new ConsultarDespachosUseCase(depsDespacho),
      autenticarUsuario: new AutenticarUsuarioUseCase(usuarios, hash, auditoria),
      consultarAuditoria: new ConsultarAuditoriaUseCase(auditoria, autorizador),
    },
    simuladorGps,
  };
}

/**
 * Em desenvolvimento o Next.js recarrega módulos (HMR) e cada rota pode ser
 * avaliada em um módulo distinto. Guardar a instância em `globalThis`
 * garante um único container (e um único simulador) por processo.
 */
const chaveGlobal = Symbol.for("sgopi.container");
type GlobalComContainer = typeof globalThis & { [chaveGlobal]?: Container };

export function obterContainer(): Container {
  const g = globalThis as GlobalComContainer;
  if (!g[chaveGlobal]) {
    g[chaveGlobal] = montarContainer();
    if ((process.env.GPS_SIMULADOR_ATIVO ?? "true") !== "false") {
      g[chaveGlobal].simuladorGps.iniciar();
    }
  }
  return g[chaveGlobal];
}
