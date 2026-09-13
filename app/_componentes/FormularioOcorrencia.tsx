"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { api, mensagemDeErro } from "@app/_lib/api";
import { FORMATOS_EVIDENCIA_ACEITOS } from "@/core/domain/ocorrencia/EvidenciaDigital";

interface EnvolvidoForm { nome: string; tipo: "VITIMA" | "TESTEMUNHA" | "SUSPEITO"; documento: string; observacoes: string }
interface EvidenciaForm { nomeArquivo: string; tamanhoBytes: number }

const TIPIFICACOES = ["Furto", "Roubo", "Lesão corporal", "Ameaça", "Violência doméstica", "Tráfico de entorpecentes", "Homicídio", "Dano", "Outro"];

// Coordenadas padrão: centro de Alegrete/RS (mesmo centro do simulador GPS).
const COORD_PADRAO = { latitude: -29.7831, longitude: -55.7918 };

export function FormularioOcorrencia() {
  const router = useRouter();
  const [tipificacao, setTipificacao] = useState(TIPIFICACOES[0]);
  const [gravidade, setGravidade] = useState<1 | 2 | 3 | 4>(2);
  const [descricaoFato, setDescricaoFato] = useState("");
  const [endereco, setEndereco] = useState({ logradouro: "", numero: "", bairro: "", cidade: "Alegrete", uf: "RS" });
  const [coordenada, setCoordenada] = useState({ latitude: String(COORD_PADRAO.latitude), longitude: String(COORD_PADRAO.longitude) });
  const [envolvidos, setEnvolvidos] = useState<EnvolvidoForm[]>([{ nome: "", tipo: "VITIMA", documento: "", observacoes: "" }]);
  const [evidencias, setEvidencias] = useState<EvidenciaForm[]>([]);
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  function atualizarEnvolvido(i: number, campo: keyof EnvolvidoForm, valor: string) {
    setEnvolvidos((lista) => lista.map((e, idx) => (idx === i ? { ...e, [campo]: valor } : e)));
  }

  function selecionarArquivos(files: FileList | null) {
    if (!files) return;
    const aceitos: EvidenciaForm[] = [];
    const rejeitados: string[] = [];
    for (const f of Array.from(files)) {
      const ext = f.name.toLowerCase().split(".").pop() ?? "";
      // UC01 Exceção II — rejeição já no cliente; o domínio revalida no servidor.
      if (FORMATOS_EVIDENCIA_ACEITOS.has(ext)) aceitos.push({ nomeArquivo: f.name, tamanhoBytes: f.size });
      else rejeitados.push(f.name);
    }
    setEvidencias((atual) => [...atual, ...aceitos]);
    setErro(rejeitados.length ? `Arquivos rejeitados (formato não suportado): ${rejeitados.join(", ")}` : null);
  }

  async function enviar(e: FormEvent) {
    e.preventDefault();
    setErro(null);
    setEnviando(true);
    try {
      const lat = Number(coordenada.latitude);
      const lng = Number(coordenada.longitude);
      const { ocorrencia } = await api<{ ocorrencia: { id: string; protocolo: string } }>("/api/ocorrencias", {
        method: "POST",
        json: {
          tipificacao,
          gravidade,
          descricaoFato,
          endereco: { ...endereco, numero: endereco.numero || undefined },
          coordenada: Number.isFinite(lat) && Number.isFinite(lng) && coordenada.latitude !== "" ? { latitude: lat, longitude: lng } : undefined,
          envolvidos: envolvidos.map((env) => ({ ...env, documento: env.documento || undefined, observacoes: env.observacoes || undefined })),
          evidencias,
        },
      });
      router.push(`/ocorrencias/${ocorrencia.id}?registrada=1`);
    } catch (err) {
      setErro(mensagemDeErro(err));
      setEnviando(false);
    }
  }

  return (
    <form onSubmit={enviar} className="cartao">
      <fieldset>
        <legend>Fato</legend>
        <div className="linha">
          <label>
            Tipificação penal
            <select value={tipificacao} onChange={(e) => setTipificacao(e.target.value)}>
              {TIPIFICACOES.map((t) => <option key={t}>{t}</option>)}
            </select>
          </label>
          <label>
            Gravidade
            <select value={gravidade} onChange={(e) => setGravidade(Number(e.target.value) as 1 | 2 | 3 | 4)}>
              <option value={1}>Baixa</option><option value={2}>Média</option><option value={3}>Alta</option><option value={4}>Crítica</option>
            </select>
          </label>
        </div>
        <label>
          Descrição circunstanciada do fato (mín. 20 caracteres)
          <textarea value={descricaoFato} onChange={(e) => setDescricaoFato(e.target.value)} required minLength={20} />
        </label>
      </fieldset>

      <fieldset>
        <legend>Local</legend>
        <div className="linha">
          <label>Logradouro<input value={endereco.logradouro} onChange={(e) => setEndereco({ ...endereco, logradouro: e.target.value })} required /></label>
          <label>Número<input value={endereco.numero} onChange={(e) => setEndereco({ ...endereco, numero: e.target.value })} /></label>
          <label>Bairro<input value={endereco.bairro} onChange={(e) => setEndereco({ ...endereco, bairro: e.target.value })} required /></label>
          <label>Cidade<input value={endereco.cidade} onChange={(e) => setEndereco({ ...endereco, cidade: e.target.value })} required /></label>
          <label>UF<input value={endereco.uf} maxLength={2} onChange={(e) => setEndereco({ ...endereco, uf: e.target.value.toUpperCase() })} required /></label>
        </div>
        <div className="linha">
          <label>Latitude<input value={coordenada.latitude} onChange={(e) => setCoordenada({ ...coordenada, latitude: e.target.value })} inputMode="decimal" /></label>
          <label>Longitude<input value={coordenada.longitude} onChange={(e) => setCoordenada({ ...coordenada, longitude: e.target.value })} inputMode="decimal" /></label>
        </div>
        <span className="pequeno">A coordenada é usada pelo cálculo de proximidade no despacho (UC02). Sem ela, o despacho não calcula distância.</span>
      </fieldset>

      <fieldset>
        <legend>Envolvidos (mínimo 1)</legend>
        {envolvidos.map((env, i) => (
          <div className="linha" key={i}>
            <label>Nome<input value={env.nome} onChange={(e) => atualizarEnvolvido(i, "nome", e.target.value)} required minLength={3} /></label>
            <label>
              Tipo
              <select value={env.tipo} onChange={(e) => atualizarEnvolvido(i, "tipo", e.target.value)}>
                <option value="VITIMA">Vítima</option><option value="TESTEMUNHA">Testemunha</option><option value="SUSPEITO">Suspeito</option>
              </select>
            </label>
            <label>Documento (CPF)<input value={env.documento} onChange={(e) => atualizarEnvolvido(i, "documento", e.target.value)} /></label>
            <label>Observações<input value={env.observacoes} onChange={(e) => atualizarEnvolvido(i, "observacoes", e.target.value)} /></label>
            <div style={{ alignSelf: "end" }}>
              <button type="button" className="secundario pequeno" disabled={envolvidos.length === 1} onClick={() => setEnvolvidos((l) => l.filter((_, idx) => idx !== i))}>Remover</button>
            </div>
          </div>
        ))}
        <div>
          <button type="button" className="secundario pequeno" onClick={() => setEnvolvidos((l) => [...l, { nome: "", tipo: "TESTEMUNHA", documento: "", observacoes: "" }])}>+ Adicionar envolvido</button>
        </div>
      </fieldset>

      <fieldset>
        <legend>Evidências digitais (opcional — .pdf, .jpg, .png)</legend>
        <input type="file" multiple accept=".pdf,.jpg,.jpeg,.png" onChange={(e) => selecionarArquivos(e.target.files)} />
        {evidencias.length > 0 && (
          <ul className="lista-simples">
            {evidencias.map((ev, i) => (
              <li key={i}>{ev.nomeArquivo} <span className="pequeno">({(ev.tamanhoBytes / 1024).toFixed(1)} KB)</span>{" "}
                <a href="#" onClick={(e) => { e.preventDefault(); setEvidencias((l) => l.filter((_, idx) => idx !== i)); }}>remover</a>
              </li>
            ))}
          </ul>
        )}
        <span className="pequeno">No MVP apenas os metadados e o hash são registrados; o binário não é enviado (limite do escopo, Seção 3.2).</span>
      </fieldset>

      {erro && <div className="aviso aviso-erro">{erro}</div>}
      <div className="acoes">
        <button type="submit" disabled={enviando}>{enviando ? "Registrando…" : "Submeter para revisão"}</button>
      </div>
    </form>
  );
}
