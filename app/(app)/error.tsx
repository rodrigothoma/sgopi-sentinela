"use client";

/** Fronteira de erro das páginas autenticadas: evita tela branca/500 crua. */
export default function ErroPagina({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <main className="conteudo">
      <div className="cartao">
        <h1>Não foi possível carregar esta página</h1>
        <p className="aviso aviso-erro">{error.message || "Erro inesperado."}</p>
        <div className="acoes">
          <button onClick={() => reset()}>Tentar novamente</button>
          <a className="botao" href="/">Início</a>
        </div>
      </div>
    </main>
  );
}
