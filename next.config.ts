import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // O núcleo (src/core) não depende do Next; apenas os adaptadores dependem.
  // Nada de configuração especial é necessária para o MVP.
  reactStrictMode: true,
};

export default nextConfig;
