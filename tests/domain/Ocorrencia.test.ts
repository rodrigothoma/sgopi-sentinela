import { describe, expect, it } from "vitest";
import { Ocorrencia } from "@/core/domain/ocorrencia/Ocorrencia";
import { DomainError, ErroTransicaoInvalida, ErroValidacao } from "@/core/domain/shared/DomainError";

const agora = new Date("2026-09-13T12:00:00Z");

function nova(extra: Partial<Parameters<typeof Ocorrencia.registrar>[0]> = {}) {
  return Ocorrencia.registrar({
    id: "o1", protocolo: "BO-2026-000001", tipificacao: "Roubo",
    descricaoFato: "Narrativa suficientemente longa para passar na validação.",
    endereco: { logradouro: "Rua A", bairro: "Centro", cidade: "Alegrete", uf: "RS" },
    envolvidos: [{ id: "e1", nome: "Fulano", tipo: "VITIMA" }],
    evidencias: [], agenteId: "ag1", gravidade: 3, criadaEm: agora, ...extra,
  });
}

describe("Ocorrencia — UC01 regras de registro", () => {
  it("nasce compulsoriamente em AGUARDANDO_REVISAO com histórico inicial (RN3)", () => {
    const o = nova();
    expect(o.status).toBe("AGUARDANDO_REVISAO");
    expect(o.paraEstado().historico).toHaveLength(1);
    expect(o.paraEstado().historico[0]).toMatchObject({ de: null, para: "AGUARDANDO_REVISAO", autorId: "ag1" });
  });

  it("exige ao menos um envolvido (RN1) e lista os campos faltantes", () => {
    expect(() => nova({ envolvidos: [] })).toThrowError(ErroValidacao);
    try {
      nova({ envolvidos: [], descricaoFato: "curta" });
    } catch (e) {
      expect((e as DomainError).detalhes?.camposFaltantes).toEqual(["descricaoFato", "envolvidos"]);
    }
  });

  it("rejeita envolvido com nome inválido", () => {
    expect(() => nova({ envolvidos: [{ id: "e1", nome: "Jo", tipo: "VITIMA" }] })).toThrowError(ErroValidacao);
  });
});

describe("Ocorrencia — máquina de estados (Seção 3.2 / UC02 / UC04)", () => {
  it("AGUARDANDO_REVISAO → VALIDADA sela a narrativa com hash", () => {
    const v = nova().validar("del1", "Deferido.", "hash123", agora);
    expect(v.status).toBe("VALIDADA");
    expect(v.paraEstado().hashIntegridade).toBe("hash123");
    expect(v.podeSerDespachada()).toBe(true);
  });

  it("validar exige despacho da autoridade", () => {
    expect(() => nova().validar("del1", "  ", "h", agora)).toThrowError(ErroValidacao);
  });

  it("devolução exige justificativa técnica (UC04 RN3)", () => {
    expect(() => nova().devolverParaCorrecao("del1", "curto", agora)).toThrowError(ErroValidacao);
    const d = nova().devolverParaCorrecao("del1", "Faltam dados do suspeito.", agora);
    expect(d.status).toBe("EM_CORRECAO");
    expect(d.paraEstado().pendenciasCorrecao).toBe("Faltam dados do suspeito.");
  });

  it("agente autor corrige e reenvia; outro agente não pode", () => {
    const d = nova().devolverParaCorrecao("del1", "Faltam dados do suspeito.", agora);
    expect(() => d.corrigirEReenviar("outro", "Nova narrativa com os dados do suspeito.", agora)).toThrowError(DomainError);
    const r = d.corrigirEReenviar("ag1", "Nova narrativa com os dados do suspeito.", agora);
    expect(r.status).toBe("AGUARDANDO_REVISAO");
    expect(r.descricaoFato).toContain("Nova narrativa");
  });

  it("não permite despachar ocorrência não validada nem validar duas vezes", () => {
    expect(() => nova().iniciarAtendimento("op", agora)).toThrowError(DomainError);
    const v = nova().validar("del1", "Ok.", "h", agora);
    expect(() => v.validar("del1", "Ok.", "h", agora)).toThrowError(ErroTransicaoInvalida);
  });

  it("VALIDADA → EM_ATENDIMENTO → CONCLUIDA", () => {
    const c = nova().validar("del1", "Ok.", "h", agora).iniciarAtendimento("op", agora).concluir("op", agora);
    expect(c.status).toBe("CONCLUIDA");
    expect(c.paraEstado().historico.map((h) => h.para)).toEqual(["AGUARDANDO_REVISAO", "VALIDADA", "EM_ATENDIMENTO", "CONCLUIDA"]);
  });

  it("é imutável: métodos devolvem nova instância", () => {
    const o = nova();
    const v = o.validar("del1", "Ok.", "h", agora);
    expect(o.status).toBe("AGUARDANDO_REVISAO");
    expect(v).not.toBe(o);
  });
});
