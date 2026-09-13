import { describe, expect, it } from "vitest";
import { criarTokenSessao, lerTokenSessao } from "@/adapters/inbound/next/sessao";

const ator = { id: "u1", nome: "Teste", papel: "DELEGADO" as const };

describe("Sessão assinada (RNF02)", () => {
  it("token válido devolve o ator", () => {
    expect(lerTokenSessao(criarTokenSessao(ator))).toEqual(ator);
  });

  it("assinatura adulterada é rejeitada", () => {
    const [corpo] = criarTokenSessao(ator).split(".");
    expect(lerTokenSessao(`${corpo}.assinaturafalsa`)).toBeNull();
  });

  it("payload adulterado (elevação de papel) é rejeitado", () => {
    const [, assinatura] = criarTokenSessao({ ...ator, papel: "AGENTE" }).split(".");
    const corpoForjado = Buffer.from(JSON.stringify({ ...ator, papel: "DELEGADO", exp: 9999999999 })).toString("base64url");
    expect(lerTokenSessao(`${corpoForjado}.${assinatura}`)).toBeNull();
  });

  it("token expirado é rejeitado", () => {
    const t = criarTokenSessao(ator, Date.now() - 9 * 3600 * 1000);
    expect(lerTokenSessao(t)).toBeNull();
  });
});
