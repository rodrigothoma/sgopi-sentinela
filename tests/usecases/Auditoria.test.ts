import { describe, expect, it } from "vitest";
import { AuditoriaHashChain } from "@/adapters/outbound/auditoria/AuditoriaHashChain";
import { HashFake, RelogioFixo } from "../apoio/fakes";

function novoLog() {
  return new AuditoriaHashChain(new HashFake(), new RelogioFixo());
}
const base = { atorId: "u", atorPapel: "AGENTE", acao: "x", recursoTipo: "t", recursoId: "1", resultado: "SUCESSO" as const };

describe("RNF03 — Auditoria encadeada por hash", () => {
  it("encadeia hashAnterior → hash e numera sequencialmente", async () => {
    const log = novoLog();
    const r1 = await log.registrar(base);
    const r2 = await log.registrar({ ...base, acao: "y" });
    expect(r1.sequencia).toBe(1);
    expect(r1.hashAnterior).toBe("0".repeat(64));
    expect(r2.sequencia).toBe(2);
    expect(r2.hashAnterior).toBe(r1.hash);
    expect(await log.verificarIntegridade()).toEqual({ integra: true });
  });

  it("registros são imutáveis (congelados)", async () => {
    const log = novoLog();
    const r = await log.registrar(base);
    expect(Object.isFrozen(r)).toBe(true);
  });

  it("gravações concorrentes não bifurcam a cadeia", async () => {
    const log = novoLog();
    await Promise.all(Array.from({ length: 20 }, (_, i) => log.registrar({ ...base, acao: `a${i}` })));
    const todos = (await log.listar(100)).reverse();
    expect(todos.map((r) => r.sequencia)).toEqual(Array.from({ length: 20 }, (_, i) => i + 1));
    for (let i = 1; i < todos.length; i++) expect(todos[i].hashAnterior).toBe(todos[i - 1].hash);
    expect((await log.verificarIntegridade()).integra).toBe(true);
  });

  it("detecta adulteração de um registro intermediário", async () => {
    const log = novoLog();
    await log.registrar(base);
    const r2 = await log.registrar({ ...base, acao: "y" });
    await log.registrar({ ...base, acao: "z" });
    // Simula adulteração direta no armazenamento (bypass do adaptador).
    const interno = (log as unknown as { registros: Array<Record<string, unknown>> }).registros;
    interno[1] = { ...r2, acao: "ADULTERADO" };
    expect(await log.verificarIntegridade()).toEqual({ integra: false, sequenciaCorrompida: 2 });
  });
});
