import { beforeEach, describe, expect, it } from "vitest";
import {
  ConsultarOcorrenciasUseCase, DevolverOcorrenciaUseCase, RegistrarOcorrenciaUseCase, ValidarOcorrenciaUseCase, CorrigirOcorrenciaUseCase,
} from "@/core/application/usecases/OcorrenciaUseCases";
import {
  AtualizarTelemetriaUseCase, DespacharViaturaUseCase, SugerirViaturasProximasUseCase, ConsultarViaturasUseCase,
} from "@/core/application/usecases/DespachoUseCases";
import { ATOR_SISTEMA } from "@/core/application/seguranca/Ator";
import { criarCoordenada } from "@/core/domain/shared/Coordenada";
import { DomainError, ErroNaoAutorizado, ErroPreCondicao, ErroValidacao } from "@/core/domain/shared/DomainError";
import { AGENTE, DELEGADO, OPERADOR, OUTRO_AGENTE, SUPERVISOR, comandoOcorrenciaValido, montarAmbiente } from "../apoio/fakes";

type Ambiente = ReturnType<typeof montarAmbiente>;

function casosDeUso(a: Ambiente) {
  const depsO = { ocorrencias: a.ocorrencias, auditoria: a.auditoria, relogio: a.relogio, ids: a.ids, hash: a.hash, eventos: a.eventos, autorizador: a.autorizador };
  const depsD = { ...depsO, viaturas: a.viaturas, despachos: a.despachos };
  return {
    registrar: new RegistrarOcorrenciaUseCase(depsO),
    consultar: new ConsultarOcorrenciasUseCase(depsO),
    validar: new ValidarOcorrenciaUseCase(depsO),
    devolver: new DevolverOcorrenciaUseCase(depsO),
    corrigir: new CorrigirOcorrenciaUseCase(depsO),
    telemetria: new AtualizarTelemetriaUseCase(depsD),
    viaturas: new ConsultarViaturasUseCase(depsD),
    sugerir: new SugerirViaturasProximasUseCase(depsD),
    despachar: new DespacharViaturaUseCase(depsD),
  };
}

let a: Ambiente;
let uc: ReturnType<typeof casosDeUso>;

beforeEach(() => {
  a = montarAmbiente();
  uc = casosDeUso(a);
});

describe("UC01 — Registrar ocorrência", () => {
  it("persiste com protocolo único sequencial e status AGUARDANDO_REVISAO", async () => {
    const o1 = await uc.registrar.executar(AGENTE, comandoOcorrenciaValido());
    const o2 = await uc.registrar.executar(AGENTE, comandoOcorrenciaValido());
    expect(o1.protocolo).toBe("BO-2026-000001");
    expect(o2.protocolo).toBe("BO-2026-000002");
    expect(o1.status).toBe("AGUARDANDO_REVISAO");
    expect(o1.envolvidos[0].id).toBeDefined();
    expect(a.eventos.tipos()).toEqual(["ocorrencia.alterada", "ocorrencia.alterada"]);
  });

  it("registra auditoria de sucesso", async () => {
    await uc.registrar.executar(AGENTE, comandoOcorrenciaValido());
    const [reg] = await a.auditoria.listar();
    expect(reg).toMatchObject({ acao: "ocorrencia.registrar", resultado: "SUCESSO", atorId: AGENTE.id });
  });

  it("rejeita evidência com formato não suportado (Exceção II) sem persistir nada", async () => {
    await expect(
      uc.registrar.executar(AGENTE, comandoOcorrenciaValido({ evidencias: [{ nomeArquivo: "virus.exe", tamanhoBytes: 10 }] })),
    ).rejects.toThrowError(ErroValidacao);
    expect(await a.ocorrencias.listar()).toHaveLength(0);
  });

  it("aceita .pdf/.jpg/.png e grava hash + mime", async () => {
    const o = await uc.registrar.executar(AGENTE, comandoOcorrenciaValido({ evidencias: [{ nomeArquivo: "foto.JPG", tamanhoBytes: 1234 }] }));
    expect(o.evidencias[0]).toMatchObject({ tipoMime: "image/jpeg" });
    expect(o.evidencias[0].hashConteudo).toMatch(/^h/);
  });

  it("apenas AGENTE registra (RNF02) e a negação é auditada", async () => {
    await expect(uc.registrar.executar(DELEGADO, comandoOcorrenciaValido())).rejects.toThrowError(ErroNaoAutorizado);
    const [reg] = await a.auditoria.listar();
    expect(reg).toMatchObject({ resultado: "NEGADO", acao: "ocorrencia.registrar", atorPapel: "DELEGADO" });
  });

  it("agente só enxerga as próprias ocorrências; delegado enxerga todas", async () => {
    await uc.registrar.executar(AGENTE, comandoOcorrenciaValido());
    await uc.registrar.executar(OUTRO_AGENTE, comandoOcorrenciaValido());
    expect(await uc.consultar.listar(AGENTE)).toHaveLength(1);
    expect(await uc.consultar.listar(DELEGADO)).toHaveLength(2);
    const [minha] = await uc.consultar.listar(OUTRO_AGENTE);
    await expect(uc.consultar.obter(AGENTE, minha.id)).rejects.toThrowError(DomainError);
  });

  it("fila do delegado vem ordenada por gravidade desc e antiguidade asc", async () => {
    const baixa = await uc.registrar.executar(AGENTE, comandoOcorrenciaValido({ gravidade: 1 }));
    a.relogio.avancar(1000);
    const critica = await uc.registrar.executar(AGENTE, comandoOcorrenciaValido({ gravidade: 4 }));
    a.relogio.avancar(1000);
    const critica2 = await uc.registrar.executar(AGENTE, comandoOcorrenciaValido({ gravidade: 4 }));
    const fila = await uc.consultar.listar(DELEGADO, { status: ["AGUARDANDO_REVISAO"] });
    expect(fila.map((o) => o.id)).toEqual([critica.id, critica2.id, baixa.id]);
  });
});

describe("UC04 — Validar ocorrência", () => {
  it("somente DELEGADO valida; tentativa de AGENTE gera alerta de segurança auditado (Exceção I)", async () => {
    const o = await uc.registrar.executar(AGENTE, comandoOcorrenciaValido());
    await expect(uc.validar.executar(AGENTE, o.id, "ok")).rejects.toThrowError(ErroNaoAutorizado);
    await expect(uc.validar.executar(OPERADOR, o.id, "ok")).rejects.toThrowError(ErroNaoAutorizado);
    const negados = (await a.auditoria.listar()).filter((r) => r.resultado === "NEGADO");
    expect(negados).toHaveLength(2);
    expect(negados[0].detalhes).toMatchObject({ alertaSeguranca: true });
  });

  it("validação gera hash de integridade da narrativa (RN2) e publica evento", async () => {
    const o = await uc.registrar.executar(AGENTE, comandoOcorrenciaValido());
    const v = await uc.validar.executar(DELEGADO, o.id, "Tipificação adequada.");
    expect(v.status).toBe("VALIDADA");
    expect(v.hashIntegridade).toBe(a.hash.sha256(`${o.id}|${o.descricaoFato}`));
    expect(v.delegadoId).toBe(DELEGADO.id);
    expect(a.eventos.publicados.at(-1)?.payload).toMatchObject({ status: "VALIDADA" });
  });

  it("devolução → correção pelo agente → nova revisão (Cenário Alternativo I)", async () => {
    const o = await uc.registrar.executar(AGENTE, comandoOcorrenciaValido());
    const d = await uc.devolver.executar(DELEGADO, o.id, "Qualificar o suspeito com apelido e vestimenta.");
    expect(d.status).toBe("EM_CORRECAO");
    await expect(uc.corrigir.executar(OUTRO_AGENTE, o.id, "Narrativa corrigida com apelido e vestimenta do suspeito.")).rejects.toThrowError(DomainError);
    const c = await uc.corrigir.executar(AGENTE, o.id, "Narrativa corrigida com apelido e vestimenta do suspeito.");
    expect(c.status).toBe("AGUARDANDO_REVISAO");
    expect(c.pendenciasCorrecao).toBeUndefined();
    const v = await uc.validar.executar(DELEGADO, o.id, "Deferido.");
    expect(v.status).toBe("VALIDADA");
    expect(v.historico.map((h) => h.para)).toEqual(["AGUARDANDO_REVISAO", "EM_CORRECAO", "AGUARDANDO_REVISAO", "VALIDADA"]);
  });

  it("ocorrência inexistente → NAO_ENCONTRADO", async () => {
    await expect(uc.validar.executar(DELEGADO, "nao-existe", "ok")).rejects.toMatchObject({ codigo: "NAO_ENCONTRADO" });
  });
});

describe("UC02 — Despacho tático", () => {
  const alvo = criarCoordenada(-29.7831, -55.7918); // ocorrência
  const perto = criarCoordenada(-29.7840, -55.7920); // ~100 m
  const medio = criarCoordenada(-29.7900, -55.8000); // ~1,1 km
  const longe = criarCoordenada(-29.8100, -55.8300); // ~4,7 km

  async function ocorrenciaValidada() {
    const o = await uc.registrar.executar(AGENTE, comandoOcorrenciaValido({ coordenada: alvo }));
    return uc.validar.executar(DELEGADO, o.id, "Deferido.");
  }

  it("telemetria atualiza posição e publica evento; papel sem permissão é negado", async () => {
    await uc.telemetria.executar(ATOR_SISTEMA, "v1", perto);
    const [v1] = (await uc.viaturas.listar(OPERADOR)).filter((v) => v.id === "v1");
    expect(v1.ultimaPosicao?.coordenada).toEqual(perto);
    expect(v1.sinalGpsValido).toBe(true);
    expect(a.eventos.tipos()).toContain("viatura.posicao");
    await expect(uc.telemetria.executar(AGENTE, "v1", perto)).rejects.toThrowError(ErroNaoAutorizado);
  });

  it("sugere as 3 viaturas disponíveis mais próximas em ordem de distância (passo 4)", async () => {
    const o = await ocorrenciaValidada();
    await uc.telemetria.executar(ATOR_SISTEMA, "v1", longe);
    await uc.telemetria.executar(ATOR_SISTEMA, "v2", perto);
    await uc.telemetria.executar(ATOR_SISTEMA, "v3", medio);
    await uc.telemetria.executar(ATOR_SISTEMA, "v4", perto); // INDISPONIVEL — não entra

    const r = await uc.sugerir.executar(OPERADOR, o.id);
    expect(r.sugestoes.map((s) => s.viatura.id)).toEqual(["v2", "v3", "v1"]);
    expect(r.sugestoes[0].distanciaKm).toBeLessThan(0.2);
    expect(r.despachoAutomaticoBloqueado).toBe(false);
  });

  it("recusa sugerir/despachar para ocorrência não validada (RN2)", async () => {
    const o = await uc.registrar.executar(AGENTE, comandoOcorrenciaValido());
    await expect(uc.sugerir.executar(OPERADOR, o.id)).rejects.toThrowError(ErroPreCondicao);
    await expect(uc.despachar.executar(OPERADOR, { ocorrenciaId: o.id, viaturaId: "v1" })).rejects.toThrowError(DomainError);
  });

  it("despacho automático: altera viatura e ocorrência, grava ordem completa e audita (passos 5–9)", async () => {
    const o = await ocorrenciaValidada();
    await uc.telemetria.executar(ATOR_SISTEMA, "v2", perto);

    const ordem = await uc.despachar.executar(OPERADOR, { ocorrenciaId: o.id, viaturaId: "v2" });
    expect(ordem).toMatchObject({ ocorrenciaId: o.id, viaturaId: "v2", operadorId: OPERADOR.id, modo: "AUTOMATICO", protocoloOcorrencia: o.protocolo });
    expect(ordem.emitidaEm).toEqual(a.relogio.agora());
    expect(ordem.distanciaKm).toBeLessThan(0.2);

    expect((await a.viaturas.obterPorId("v2"))?.status).toBe("EM_DESLOCAMENTO");
    expect((await a.ocorrencias.obterPorId(o.id))?.status).toBe("EM_ATENDIMENTO");
    expect(await a.despachos.listarPorOcorrencia(o.id)).toHaveLength(1);

    const reg = (await a.auditoria.listar()).find((r) => r.acao === "despacho.emitir");
    expect(reg).toMatchObject({ resultado: "SUCESSO", atorId: OPERADOR.id });
    expect(a.eventos.tipos().slice(-2)).toEqual(["viatura.despachada", "ocorrencia.alterada"]);
  });

  it("só OPERADOR_CENTRAL emite despacho (RNF02)", async () => {
    const o = await ocorrenciaValidada();
    await uc.telemetria.executar(ATOR_SISTEMA, "v1", perto);
    await expect(uc.despachar.executar(SUPERVISOR, { ocorrenciaId: o.id, viaturaId: "v1" })).rejects.toThrowError(ErroNaoAutorizado);
    await expect(uc.despachar.executar(DELEGADO, { ocorrenciaId: o.id, viaturaId: "v1" })).rejects.toThrowError(ErroNaoAutorizado);
  });

  it("viatura já despachada não pode ser despachada de novo (RN1)", async () => {
    const o1 = await ocorrenciaValidada();
    const o2 = await ocorrenciaValidada();
    await uc.telemetria.executar(ATOR_SISTEMA, "v1", perto);
    await uc.despachar.executar(OPERADOR, { ocorrenciaId: o1.id, viaturaId: "v1" });
    await expect(uc.despachar.executar(OPERADOR, { ocorrenciaId: o2.id, viaturaId: "v1" })).rejects.toThrowError(ErroPreCondicao);
    // A ocorrência o2 continua VALIDADA (nada foi gravado parcialmente).
    expect((await a.ocorrencias.obterPorId(o2.id))?.status).toBe("VALIDADA");
  });

  describe("RNF04 — falha de GPS (Exceção I)", () => {
    it("GPS > 60 s: sinal inválido, sugestão sem distância e despacho automático bloqueado", async () => {
      const o = await ocorrenciaValidada();
      await uc.telemetria.executar(ATOR_SISTEMA, "v1", perto);
      a.relogio.avancar(61_000);

      const r = await uc.sugerir.executar(OPERADOR, o.id);
      expect(r.despachoAutomaticoBloqueado).toBe(true);
      expect(r.sugestoes.find((s) => s.viatura.id === "v1")).toMatchObject({ distanciaKm: null, viatura: { sinalGpsValido: false } });

      await expect(uc.despachar.executar(OPERADOR, { ocorrenciaId: o.id, viaturaId: "v1" })).rejects.toMatchObject({
        codigo: "PRE_CONDICAO", detalhes: { motivo: "GPS_DESATUALIZADO" },
      });
    });

    it("despacho manual com posição informada via rádio é aceito e registrado como MANUAL", async () => {
      const o = await ocorrenciaValidada();
      await uc.telemetria.executar(ATOR_SISTEMA, "v1", perto);
      a.relogio.avancar(120_000);

      const ordem = await uc.despachar.executar(OPERADOR, { ocorrenciaId: o.id, viaturaId: "v1", posicaoInformada: medio, observacao: "Posição via rádio" });
      expect(ordem.modo).toBe("MANUAL_POSICAO_INFORMADA");
      expect(ordem.posicaoInformada).toEqual(medio);
      expect(ordem.distanciaKm).toBeGreaterThan(0.9);
    });

    it("viaturas com GPS válido são priorizadas sobre as sem sinal", async () => {
      const o = await ocorrenciaValidada();
      await uc.telemetria.executar(ATOR_SISTEMA, "v1", perto);
      a.relogio.avancar(61_000);
      await uc.telemetria.executar(ATOR_SISTEMA, "v2", longe);
      const r = await uc.sugerir.executar(OPERADOR, o.id);
      expect(r.sugestoes.map((s) => s.viatura.id)).toEqual(["v2", "v1", "v3"]);
      expect(r.despachoAutomaticoBloqueado).toBe(false);
    });
  });

  it("nenhuma viatura disponível → lista vazia sem bloqueio (Exceção II)", async () => {
    const o = await ocorrenciaValidada();
    for (const id of ["v1", "v2", "v3"]) {
      await uc.telemetria.executar(ATOR_SISTEMA, id, perto);
      const outra = await ocorrenciaValidada();
      await uc.despachar.executar(OPERADOR, { ocorrenciaId: outra.id, viaturaId: id });
    }
    const r = await uc.sugerir.executar(OPERADOR, o.id);
    expect(r.sugestoes).toHaveLength(0);
    expect(r.despachoAutomaticoBloqueado).toBe(false);
  });
});
