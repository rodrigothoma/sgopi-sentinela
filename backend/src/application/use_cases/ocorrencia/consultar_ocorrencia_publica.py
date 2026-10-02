"""
Caso de uso: ConsultarOcorrenciaPublica (RF01 — acompanhamento do cidadão pelo protocolo).

Público por definição (sem ator). Ocorrência excluída logicamente é tratada como inexistente
(RNF03*: ela some das listagens) e a saída não carrega dados pessoais nem textos livres (LGPD).
"""
from application.ports.inbound.interface_consultar_ocorrencia_publica import (
    ConsultaPublicaOutput,
    InterfaceConsultarOcorrenciaPublica,
)
from application.ports.outbound.repositorio_ocorrencia import RepositorioOcorrencia
from domain.ocorrencia.status import StatusOcorrencia
from domain.shared.exceptions import EntidadeNaoEncontradaError


class ConsultarOcorrenciaPublica(InterfaceConsultarOcorrenciaPublica):
    def __init__(self, repositorio: RepositorioOcorrencia) -> None:
        self._repositorio = repositorio

    async def executar(self, numero_protocolo: str) -> ConsultaPublicaOutput:
        protocolo = (numero_protocolo or "").strip().upper()
        ocorrencia = await self._repositorio.buscar_por_protocolo(protocolo) if protocolo else None
        if ocorrencia is None or ocorrencia.status == StatusOcorrencia.EXCLUIDA:
            raise EntidadeNaoEncontradaError(
                f"Protocolo {protocolo} não encontrado.", chave="ocorrencia.protocolo_nao_encontrado"
            )
        return ConsultaPublicaOutput(
            numero_protocolo=ocorrencia.numero_protocolo,
            status=ocorrencia.status.value,
            natureza=ocorrencia.natureza,
            localizacao=ocorrencia.localizacao,
            criada_em=ocorrencia.criada_em.isoformat(),
        )
