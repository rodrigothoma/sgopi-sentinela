import Link from "next/link";
import { redirect } from "next/navigation";
import { atorDaSessao } from "@/adapters/inbound/next/sessao";
import { MENU, ROTULO_PAPEL } from "@app/_lib/navegacao";
import { BotaoSair } from "@app/_componentes/BotaoSair";

/**
 * Layout autenticado. A checagem de sessão aqui protege as páginas; a
 * checagem de papel por ação continua nos casos de uso (defesa em profundidade).
 */
export default async function LayoutAutenticado({ children }: { children: React.ReactNode }) {
  const ator = await atorDaSessao();
  if (!ator) redirect("/login");

  return (
    <>
      <header className="topo">
        <span className="marca">🛡️ SGOPI Sentinela</span>
        <nav>
          {MENU.filter((i) => i.papeis.includes(ator.papel)).map((i) => (
            <Link key={i.href} href={i.href}>{i.rotulo}</Link>
          ))}
        </nav>
        <div className="usuario">
          <span>{ator.nome} · {ROTULO_PAPEL[ator.papel]}</span>
          <BotaoSair />
        </div>
      </header>
      {children}
    </>
  );
}
