import { NextResponse } from "next/server";
import { obterContainer } from "@/config/container";
import { esquemaLogin } from "@/adapters/inbound/http/esquemas";
import { respostaErro } from "@/adapters/inbound/http/respostas";
import { gravarSessao } from "@/adapters/inbound/next/sessao";

export async function POST(req: Request) {
  try {
    const { matricula, senha } = esquemaLogin.parse(await req.json());
    const ator = await obterContainer().casosDeUso.autenticarUsuario.executar(matricula, senha);
    await gravarSessao(ator);
    return NextResponse.json({ ator });
  } catch (erro) {
    return respostaErro(erro);
  }
}
