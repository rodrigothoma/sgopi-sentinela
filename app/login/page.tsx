"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { api, mensagemDeErro } from "@app/_lib/api";
import { rotaInicialPorPapel } from "@app/_lib/navegacao";
import type { Ator } from "@/core/application/seguranca/Ator";

const CONTAS_DEMO = [
  ["agente", "Agente Policial"],
  ["delegado", "Delegado"],
  ["operador", "Operador de Central"],
  ["supervisor", "Supervisor"],
];

export default function PaginaLogin() {
  const router = useRouter();
  const [matricula, setMatricula] = useState("");
  const [senha, setSenha] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  async function entrar(e: FormEvent) {
    e.preventDefault();
    setErro(null);
    setEnviando(true);
    try {
      const { ator } = await api<{ ator: Ator }>("/api/auth/login", { method: "POST", json: { matricula, senha } });
      router.replace(rotaInicialPorPapel(ator.papel));
      router.refresh();
    } catch (err) {
      setErro(mensagemDeErro(err));
    } finally {
      setEnviando(false);
    }
  }

  return (
    <main className="conteudo">
      <div className="cartao login-caixa">
        <h1>🛡️ SGOPI Sentinela</h1>
        <p className="sub">Acesso restrito a servidores autenticados (RNF02).</p>
        <form onSubmit={entrar}>
          <label>
            Matrícula
            <input value={matricula} onChange={(e) => setMatricula(e.target.value)} autoComplete="username" required />
          </label>
          <label>
            Senha
            <input type="password" value={senha} onChange={(e) => setSenha(e.target.value)} autoComplete="current-password" required />
          </label>
          {erro && <div className="aviso aviso-erro">{erro}</div>}
          <button type="submit" disabled={enviando}>{enviando ? "Entrando…" : "Entrar"}</button>
        </form>
        <p className="pequeno" style={{ marginTop: 16 }}>
          Contas de demonstração (senha <code>sgopi123</code>):{" "}
          {CONTAS_DEMO.map(([m, r], i) => (
            <span key={m}>
              {i > 0 && " · "}
              <a href="#" onClick={(e) => { e.preventDefault(); setMatricula(m); setSenha("sgopi123"); }}>{m}</a> ({r})
            </span>
          ))}
        </p>
      </div>
    </main>
  );
}
