import { describe, expect, it } from "vitest";
import { Viatura, TOLERANCIA_SINAL_GPS_MS } from "@/core/domain/viatura/Viatura";
import { criarCoordenada, distanciaHaversineKm } from "@/core/domain/shared/Coordenada";
import { ErroPreCondicao, ErroValidacao } from "@/core/domain/shared/DomainError";

const t0 = new Date("2026-09-13T12:00:00Z");
const v = () => Viatura.reidratar({ id: "v1", prefixo: "VTR-1", placa: "X", equipe: "A", status: "DISPONIVEL" });

describe("Viatura — telemetria e RNF04", () => {
  it("sem posição, o sinal é inválido", () => {
    expect(v().sinalGpsValido(t0)).toBe(false);
  });

  it("sinal válido até 60 s; inválido após (UC02 RN3)", () => {
    const c = v().atualizarPosicao(criarCoordenada(-29.78, -55.79), t0);
    expect(c.sinalGpsValido(new Date(t0.getTime() + TOLERANCIA_SINAL_GPS_MS))).toBe(true);
    expect(c.sinalGpsValido(new Date(t0.getTime() + TOLERANCIA_SINAL_GPS_MS + 1))).toBe(false);
  });

  it("ignora telemetria fora de ordem (mais antiga que a atual)", () => {
    const c = v().atualizarPosicao(criarCoordenada(-29.78, -55.79), t0);
    const antiga = c.atualizarPosicao(criarCoordenada(0, 0), new Date(t0.getTime() - 5000));
    expect(antiga.ultimaPosicao?.coordenada.latitude).toBe(-29.78);
  });

  it("só viatura DISPONIVEL pode ser despachada (UC02 RN1)", () => {
    const d = v().despachar("o1");
    expect(d.status).toBe("EM_DESLOCAMENTO");
    expect(() => d.despachar("o2")).toThrowError(ErroPreCondicao);
  });
});

describe("Coordenada / Haversine", () => {
  it("valida faixas de latitude e longitude", () => {
    expect(() => criarCoordenada(91, 0)).toThrowError(ErroValidacao);
    expect(() => criarCoordenada(0, -181)).toThrowError(ErroValidacao);
  });

  it("distância entre Alegrete e Porto Alegre ≈ 430 km", () => {
    const d = distanciaHaversineKm(criarCoordenada(-29.7831, -55.7918), criarCoordenada(-30.0346, -51.2177));
    expect(d).toBeGreaterThan(425);
    expect(d).toBeLessThan(445);
  });

  it("distância de um ponto a ele mesmo é 0", () => {
    const p = criarCoordenada(-29.78, -55.79);
    expect(distanciaHaversineKm(p, p)).toBe(0);
  });
});
