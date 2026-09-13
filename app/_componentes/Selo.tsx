import { ROTULO_STATUS, type StatusOcorrencia } from "@/core/domain/ocorrencia/StatusOcorrencia";

export function SeloStatus({ status }: { status: StatusOcorrencia }) {
  return <span className={`selo selo-${status}`}>{ROTULO_STATUS[status]}</span>;
}

const ROTULO_VIATURA: Record<string, string> = {
  DISPONIVEL: "Disponível", EM_DESLOCAMENTO: "Em deslocamento", EM_ATENDIMENTO: "Em atendimento", INDISPONIVEL: "Indisponível",
};
export function SeloViatura({ status }: { status: string }) {
  return <span className={`selo selo-${status}`}>{ROTULO_VIATURA[status] ?? status}</span>;
}

export function SeloGps({ valido }: { valido: boolean }) {
  return <span className={`selo ${valido ? "selo-gps-ok" : "selo-gps-falha"}`}>{valido ? "GPS ok" : "GPS sem sinal"}</span>;
}
