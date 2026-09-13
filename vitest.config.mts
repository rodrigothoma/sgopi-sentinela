import { defineConfig } from "vitest/config";

// Os testes cobrem exclusivamente o núcleo hexagonal (domínio + casos de uso),
// que não depende do Next.js nem de banco de dados — conforme a Seção 7.1 da
// Documentação de Engenharia.
export default defineConfig({
  test: {
    include: ["tests/**/*.test.ts"],
    environment: "node",
  },
  resolve: {
    alias: {
      "@": new URL("./src", import.meta.url).pathname,
    },
  },
});
