import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SGOPI Sentinela",
  description: "Sistema de Gestão de Ocorrências Policiais Integradas — MVP",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
