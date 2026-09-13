"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import type { Ator } from "@/core/application/seguranca/Ator";
import type { EstadoOcorrencia } from "@/core/domain/ocorrencia/Ocorrencia";
import { api, mensagemDeErro } from "@app/_lib/api";
import type { Serializado } from "@app/_lib/formatos";

/**
 * Ações contextuais por papel/estado (UC04 e correção pelo Agente).
 * O servidor sempre revalida a autorização; o componente só evita mostrar
 * botões inúteis.
 */
export function AcoesOcorrencia({ ator, ocorrencia }: { ator: Ator; ocorrencia: Serializado<EstadoOcorrencia> }) {
  const router = useRouter();
  const [despacho, setDespacho] = useState("");
  const [pendencias, setPendencias] = useState("");
  const [novaDescricao, setNovaDescricao] = useState(ocorrencia.descricaoFato);
  const [erro, setErro] = useState<string | null>(null);
  const [ocupado, setOcupado] = useState(false);

  async function executar(caminho: string, json: unknown) {
    setErro(null);
    setOcupado(true);
    try {
      await api(caminho, { method: "POST", json });
      router.refresh();
    } catch (e) {
      setErro(mensagemDeErro(e));
    } finally {
      setOcupado(false);
    }
  }

  const ehDelegadoRevisando = ator.papel === "DELEGADO" && ocorrencia.status === "AGUARDANDO_REVISAO";
  const ehAgenteCorrigindo = ator.papel === "AGENTE" && ocorrencia.status === "EM_CORRECAO" && ocorrencia.agenteId === ator.id;

  if (!ehDelegadoRevisando && !ehAgenteCorrigindo) return null;

  return (
    <section className="cartao">
      {ehDelegadoRevisando && (
        <>
          <h2 style={{ marginTop: 0 }}>Revisão do Delegado (UC04)</h2>
          <form onSubmit={(e) => { e.preventDefault(); void executar(`/api/ocorrencias/${ocorrencia.id}/validar`, { despachoAutoridade: despacho }); }}>
            <label>
              Despacho da autoridade (obrigatório para validar)
              <textarea value={despacho} onChange={(e) => setDespacho(e.target.value)} placeholder="Ex.: Tipificação adequada. Encaminhe-se ao painel tático para atendimento." />
            </label>
            <div className="acoes">
              <button type="submit" disabled={ocupado || !despacho.trim()}>✓ Validar ocorrência</button>
            </div>
          </form>
          <hr style={{ border: 0, borderTop: "1px solid var(--borda)", margin: "16px 0" }} />
          <form onSubmit={(e) => { e.preventDefault(); void executar(`/api/ocorrencias/${ocorrencia.id}/devolver`, { pendencias }); }}>
            <label>
              Devolver para correção — pendências (mín. 10 caracteres)
              <textarea value={pendencias} onChange={(e) => setPendencias(e.target.value)} placeholder="Descreva as inconsistências a sanar." />
            </label>
            <div className="acoes">
              <button type="submit" className="perigo" disabled={ocupado || pendencias.trim().length < 10}>↩ Devolver ao Agente</button>
            </div>
          </form>
        </>
      )}

      {ehAgenteCorrigindo && (
        <>
          <h2 style={{ marginTop: 0 }}>Sanar pendências e reenviar</h2>
          <div className="aviso aviso-alerta">Pendências do Delegado: {ocorrencia.pendenciasCorrecao}</div>
          <form style={{ marginTop: 12 }} onSubmit={(e) => { e.preventDefault(); void executar(`/api/ocorrencias/${ocorrencia.id}/corrigir`, { descricaoFato: novaDescricao }); }}>
            <label>
              Nova descrição do fato
              <textarea value={novaDescricao} onChange={(e) => setNovaDescricao(e.target.value)} />
            </label>
            <div className="acoes">
              <button type="submit" disabled={ocupado}>Reenviar para revisão</button>
            </div>
          </form>
        </>
      )}
      {erro && <div className="aviso aviso-erro" style={{ marginTop: 12 }}>{erro}</div>}
    </section>
  );
}
