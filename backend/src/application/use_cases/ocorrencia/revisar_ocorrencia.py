"""
Casos de uso de revisão pelo Delegado (RF04*): ValidarOcorrencia, DevolverParaCorrecao,
RejeitarOcorrencia. Cada decisão: verifica papel, transiciona, audita, publica evento,
confirma transação. Decisão dupla é bloqueada pelo optimistic locking (RNF03).
"""
from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from uuid import UUID

from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_consultar_ocorrencias import OcorrenciaDetalheOutput
from application.ports.inbound.interface_revisar_ocorrencia import (
    DecisaoRevisaoInput,
    InterfaceDevolverParaCorrecao,
    InterfaceRejeitarOcorrencia,
    InterfaceValidarOcorrencia,
)
from application.ports.outbound.porta_auditoria import PortaAuditoria
from application.ports.outbound.publicador_eventos import PublicadorEventos
from application.ports.outbound.relogio import Relogio
from application.ports.outbound.repositorio_ocorrencia import RepositorioOcorrencia
from application.ports.outbound.unidade_de_trabalho import UnidadeDeTrabalho
from application.use_cases.ocorrencia._mapeadores import para_detalhe
from application.use_cases.ocorrencia.consultar_ocorrencias import carregar_ou_404
from domain.auditoria.entity import RegistroAuditoria
from domain.ocorrencia import eventos
from domain.ocorrencia.entity import Ocorrencia
from domain.shared.eventos import EventoDominio
from domain.usuario.entity import Papel


class _DecisaoBase:
    operacao: str
    papeis: tuple[Papel, ...] = (Papel.DELEGADO,)

    def __init__(
        self,
        repositorio: RepositorioOcorrencia,
        uow: UnidadeDeTrabalho,
        relogio: Relogio,
        auditoria: PortaAuditoria,
        publicador: PublicadorEventos,
    ) -> None:
        self._repositorio = repositorio
        self._uow = uow
        self._relogio = relogio
        self._auditoria = auditoria
        self._publicador = publicador

    def _aplicar(self, ocorrencia: Ocorrencia, ator: Ator, justificativa: str | None, agora: datetime) -> None:
        raise NotImplementedError

    def _evento(self, ocorrencia: Ocorrencia, agora: datetime) -> EventoDominio:
        raise NotImplementedError

    async def _executar_decisao(self, ator: Ator, ocorrencia_id: UUID, justificativa: str | None) -> OcorrenciaDetalheOutput:
        ator.exigir_papel(*self.papeis)
        agora = self._relogio.agora()
        async with self._uow:
            ocorrencia = await carregar_ou_404(self._repositorio, ocorrencia_id)
            antes = {"status": ocorrencia.status.value, "versao": ocorrencia.versao}
            self._aplicar(ocorrencia, ator, justificativa, agora)
            await self._repositorio.salvar(ocorrencia)
            await self._auditoria.registrar(
                RegistroAuditoria(
                    quem=ator.id,
                    quando=agora,
                    operacao=self.operacao,
                    entidade="Ocorrencia",
                    entidade_id=str(ocorrencia.id),
                    dados_antes=antes,
                    dados_depois={"status": ocorrencia.status.value, "versao": ocorrencia.versao, "justificativa": justificativa},
                    ip=ator.ip,
                )
            )
            await self._uow.commit()
        await self._publicador.publicar(self._evento(ocorrencia, agora))
        return para_detalhe(ocorrencia, ator)


class ValidarOcorrencia(_DecisaoBase, InterfaceValidarOcorrencia):
    operacao = "ocorrencia.validar"

    def _aplicar(self, ocorrencia, ator, justificativa, agora):
        ocorrencia.validar(ator.id, agora)

    def _evento(self, ocorrencia, agora):
        return eventos.ocorrencia_validada(
            ocorrencia.id, agora, numero_protocolo=ocorrencia.numero_protocolo, natureza=ocorrencia.natureza,
            latitude=ocorrencia.coordenada.latitude, longitude=ocorrencia.coordenada.longitude,
        )

    async def executar(self, ator: Ator, input_dto: DecisaoRevisaoInput) -> OcorrenciaDetalheOutput:
        return await self._executar_decisao(ator, input_dto.ocorrencia_id, None)


class DevolverParaCorrecao(_DecisaoBase, InterfaceDevolverParaCorrecao):
    operacao = "ocorrencia.devolver_para_correcao"

    def _aplicar(self, ocorrencia, ator, justificativa, agora):
        ocorrencia.devolver_para_correcao(ator.id, justificativa or "", agora)

    def _evento(self, ocorrencia, agora):
        return eventos.ocorrencia_devolvida(ocorrencia.id, agora, agente_policial_id=str(ocorrencia.agente_policial_id))

    async def executar(self, ator: Ator, input_dto: DecisaoRevisaoInput) -> OcorrenciaDetalheOutput:
        return await self._executar_decisao(ator, input_dto.ocorrencia_id, input_dto.justificativa)


class RejeitarOcorrencia(_DecisaoBase, InterfaceRejeitarOcorrencia):
    operacao = "ocorrencia.rejeitar"

    def _aplicar(self, ocorrencia, ator, justificativa, agora):
        ocorrencia.rejeitar(ator.id, justificativa or "", agora)

    def _evento(self, ocorrencia, agora):
        return eventos.ocorrencia_rejeitada(ocorrencia.id, agora, agente_policial_id=str(ocorrencia.agente_policial_id))

    async def executar(self, ator: Ator, input_dto: DecisaoRevisaoInput) -> OcorrenciaDetalheOutput:
        return await self._executar_decisao(ator, input_dto.ocorrencia_id, input_dto.justificativa)
