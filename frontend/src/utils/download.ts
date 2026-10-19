/** Extrai o nome do arquivo de ``Content-Disposition: attachment; filename="x.csv"``. */
export function nomeDoArquivo(contentDisposition: string | undefined, padrao: string): string {
  const nome = contentDisposition?.match(/filename="?([^";]+)"?/i)?.[1];
  return nome ?? padrao;
}

/** Dispara o download de um Blob no navegador. */
export function salvarBlob(blob: Blob, nome: string): void {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = nome;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}
