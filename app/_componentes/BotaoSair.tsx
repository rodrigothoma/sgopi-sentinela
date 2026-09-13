"use client";

import { useRouter } from "next/navigation";

export function BotaoSair() {
  const router = useRouter();
  return (
    <button
      className="secundario pequeno"
      onClick={async () => {
        await fetch("/api/auth/logout", { method: "POST" });
        router.replace("/login");
        router.refresh();
      }}
    >
      Sair
    </button>
  );
}
