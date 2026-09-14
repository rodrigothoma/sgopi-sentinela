"""
Casos de uso privativos do Delegado: ArquivarOcorrencia e ExcluirOcorrencia.

Reaproveitam o pipeline de decisão (papel → transição → auditoria → evento → commit).
A exclusão é lógica: a ocorrência muda para EXCLUIDA e some das listagens sem
filtro explícito, mas permanece consultável para auditoria (RNF03*).
"""
from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_arquivar_ocorrencia import (
    AutorizacaoDelegadoInput,
    InterfaceArquivarOcorrencia,
    InterfaceExcluirOcorrencia,
)
from application.ports.inbound.interface_consultar_ocorrencias import OcorrenciaDetalheOutput
from application.use_cases.ocorrencia.revisar_ocorrencia import _DecisaoBase
from domain.ocorrencia import eventos


class ArquivarOcorrencia(_DecisaoBase, InterfaceArquivarOcorrencia):
    operacao = "ocorrencia.arquivar"

    def _aplicar(self, ocorrencia, ator, justificativa, agora):
        ocorrencia.arquivar(ator.id, justificativa or "", agora)

    def _evento(self, ocorrencia, agora):
        return eventos.ocorrencia_arquivada(ocorrencia.id, agora, agente_policial_id=str(ocorrencia.agente_policial_id))

    async def executar(self, ator: Ator, input_dto: AutorizacaoDelegadoInput) -> OcorrenciaDetalheOutput:
        return await self._executar_decisao(ator, input_dto.ocorrencia_id, input_dto.motivo)


class ExcluirOcorrencia(_DecisaoBase, InterfaceExcluirOcorrencia):
    operacao = "ocorrencia.excluir"

    def _aplicar(self, ocorrencia, ator, justificativa, agora):
        ocorrencia.excluir(ator.id, justificativa or "", agora)

    def _evento(self, ocorrencia, agora):
        return eventos.ocorrencia_excluida(ocorrencia.id, agora, agente_policial_id=str(ocorrencia.agente_policial_id))

    async def executar(self, ator: Ator, input_dto: AutorizacaoDelegadoInput) -> OcorrenciaDetalheOutput:
        return await self._executar_decisao(ator, input_dto.ocorrencia_id, input_dto.motivo)
