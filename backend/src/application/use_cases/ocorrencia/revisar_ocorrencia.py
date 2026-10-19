"""
Casos de uso de revisão pelo Delegado (RF04*): ValidarOcorrencia, DevolverParaCorrecao,
RejeitarOcorrencia. Cada decisão: verifica papel, transiciona, audita, notifica o agente
autor (na mesma transação), confirma e publica os eventos. Decisão dupla é bloqueada pelo
optimistic locking (RNF03).
"""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_consultar_ocorrencias import OcorrenciaDetalheOutput
from application.ports.inbound.interface_revisar_ocorrencia import (
    DecisaoRevisaoInput,
    InterfaceDevolverParaCorrecao,
    InterfaceRejeitarOcorrencia,
    InterfaceValidarOcorrencia,
    ValidarOcorrenciaInput,
)
from application.ports.outbound.porta_auditoria import PortaAuditoria
from application.ports.outbound.publicador_eventos import PublicadorEventos
from application.ports.outbound.relogio import Relogio
from application.ports.outbound.repositorio_notificacao import RepositorioNotificacao
from application.ports.outbound.repositorio_ocorrencia import RepositorioOcorrencia
from application.ports.outbound.unidade_de_trabalho import UnidadeDeTrabalho
from application.use_cases.ocorrencia._mapeadores import para_detalhe
from application.use_cases.ocorrencia.consultar_ocorrencias import carregar_ou_404
from domain.auditoria.entity import RegistroAuditoria
from domain.notificacao.entity import Notificacao, PrioridadeNotificacao, TipoNotificacao
from domain.notificacao.eventos import notificacao_emitida
from domain.ocorrencia import eventos
from domain.ocorrencia.entity import Ocorrencia, OrigemOcorrencia
from domain.shared.eventos import EventoDominio
from domain.usuario.entity import Papel

ROTA_MINHAS_OCORRENCIAS = "/minhas"


class _DecisaoBase:
    operacao: str
    campo_texto_auditoria = "justificativa"
    papeis: tuple[Papel, ...] = (Papel.DELEGADO,)
    # Decisões que avisam o agente autor definem o título (com {protocolo}) e a prioridade
    titulo_notificacao: str | None = None
    prioridade_notificacao: PrioridadeNotificacao = PrioridadeNotificacao.MEDIA

    def __init__(
        self,
        repositorio: RepositorioOcorrencia,
        uow: UnidadeDeTrabalho,
        relogio: Relogio,
        auditoria: PortaAuditoria,
        publicador: PublicadorEventos,
        notificacoes: RepositorioNotificacao | None = None,
    ) -> None:
        self._repositorio = repositorio
        self._uow = uow
        self._relogio = relogio
        self._auditoria = auditoria
        self._publicador = publicador
        self._notificacoes = notificacoes

    def _aplicar(self, ocorrencia: Ocorrencia, ator: Ator, texto_decisao: str | None, agora: datetime) -> None:
        raise NotImplementedError

    def _evento(self, ocorrencia: Ocorrencia, agora: datetime) -> EventoDominio:
        raise NotImplementedError

    def _notificacao_ao_autor(self, ocorrencia: Ocorrencia, agora: datetime) -> Notificacao | None:
        """Aviso pessoal ao agente que lavrou a ocorrência (RF04). Comunicação do cidadão
        (origem PUBLICA) não tem agente autor a avisar — o "autor" é o usuário de sistema."""
        if self._notificacoes is None or self.titulo_notificacao is None:
            return None
        if ocorrencia.origem == OrigemOcorrencia.PUBLICA:
            return None
        protocolo = ocorrencia.numero_protocolo
        texto_decisao = ocorrencia.historico_status[-1].justificativa
        mensagem = f"{ocorrencia.natureza} — {texto_decisao}" if texto_decisao else ocorrencia.natureza
        return Notificacao.criar(
            titulo=self.titulo_notificacao.format(protocolo=protocolo),
            mensagem=mensagem,
            tipo=TipoNotificacao.REVISAO_OCORRENCIA,
            prioridade=self.prioridade_notificacao,
            usuario_id=ocorrencia.agente_policial_id,
            link=f"{ROTA_MINHAS_OCORRENCIAS}?protocolo={protocolo}&ocorrencia={ocorrencia.id}",
            metadados={
                "ocorrencia_id": str(ocorrencia.id),
                "numero_protocolo": protocolo,
                "status": ocorrencia.status.value,
            },
            instante=agora,
        )

    def _registro_auditoria(
        self, ocorrencia: Ocorrencia, ator: Ator, antes: dict[str, object], agora: datetime
    ) -> RegistroAuditoria:
        return RegistroAuditoria(
            quem=ator.id,
            quando=agora,
            operacao=self.operacao,
            entidade="Ocorrencia",
            entidade_id=str(ocorrencia.id),
            dados_antes=antes,
            dados_depois={
                "status": ocorrencia.status.value,
                "versao": ocorrencia.versao,
                self.campo_texto_auditoria: ocorrencia.historico_status[-1].justificativa,
            },
            ip=ator.ip,
        )

    async def _executar_decisao(self, ator: Ator, ocorrencia_id: UUID, texto_decisao: str | None) -> OcorrenciaDetalheOutput:
        ator.exigir_papel(*self.papeis)
        agora = self._relogio.agora()
        async with self._uow:
            ocorrencia = await carregar_ou_404(self._repositorio, ocorrencia_id)
            antes = {"status": ocorrencia.status.value, "versao": ocorrencia.versao}
            self._aplicar(ocorrencia, ator, texto_decisao, agora)
            await self._repositorio.salvar(ocorrencia)
            await self._auditoria.registrar(self._registro_auditoria(ocorrencia, ator, antes, agora))
            notificacao = self._notificacao_ao_autor(ocorrencia, agora)
            if notificacao is not None:
                await self._notificacoes.salvar(notificacao)
            await self._uow.commit()
        await self._publicador.publicar(self._evento(ocorrencia, agora))
        if notificacao is not None:
            await self._publicador.publicar(notificacao_emitida(notificacao))
        return para_detalhe(ocorrencia, ator)


class ValidarOcorrencia(_DecisaoBase, InterfaceValidarOcorrencia):
    operacao = "ocorrencia.validar"
    campo_texto_auditoria = "despacho"
    titulo_notificacao = "Ocorrência {protocolo} validada pelo Delegado"
    prioridade_notificacao = PrioridadeNotificacao.BAIXA

    def _aplicar(self, ocorrencia, ator, despacho, agora):
        ocorrencia.validar(ator.id, agora, despacho)

    def _evento(self, ocorrencia, agora):
        return eventos.ocorrencia_validada(
            ocorrencia.id, agora, numero_protocolo=ocorrencia.numero_protocolo, natureza=ocorrencia.natureza,
            latitude=ocorrencia.coordenada.latitude, longitude=ocorrencia.coordenada.longitude,
        )

    async def executar(self, ator: Ator, input_dto: ValidarOcorrenciaInput) -> OcorrenciaDetalheOutput:
        return await self._executar_decisao(ator, input_dto.ocorrencia_id, input_dto.despacho)


class DevolverParaCorrecao(_DecisaoBase, InterfaceDevolverParaCorrecao):
    operacao = "ocorrencia.devolver_para_correcao"
    titulo_notificacao = "Ocorrência {protocolo} devolvida para correção"
    prioridade_notificacao = PrioridadeNotificacao.ALTA

    def _aplicar(self, ocorrencia, ator, justificativa, agora):
        ocorrencia.devolver_para_correcao(ator.id, justificativa or "", agora)

    def _evento(self, ocorrencia, agora):
        return eventos.ocorrencia_devolvida(ocorrencia.id, agora, agente_policial_id=str(ocorrencia.agente_policial_id))

    async def executar(self, ator: Ator, input_dto: DecisaoRevisaoInput) -> OcorrenciaDetalheOutput:
        return await self._executar_decisao(ator, input_dto.ocorrencia_id, input_dto.justificativa)


class RejeitarOcorrencia(_DecisaoBase, InterfaceRejeitarOcorrencia):
    operacao = "ocorrencia.rejeitar"
    titulo_notificacao = "Ocorrência {protocolo} rejeitada pelo Delegado"

    def _aplicar(self, ocorrencia, ator, justificativa, agora):
        ocorrencia.rejeitar(ator.id, justificativa or "", agora)

    def _evento(self, ocorrencia, agora):
        return eventos.ocorrencia_rejeitada(ocorrencia.id, agora, agente_policial_id=str(ocorrencia.agente_policial_id))

    async def executar(self, ator: Ator, input_dto: DecisaoRevisaoInput) -> OcorrenciaDetalheOutput:
        return await self._executar_decisao(ator, input_dto.ocorrencia_id, input_dto.justificativa)
