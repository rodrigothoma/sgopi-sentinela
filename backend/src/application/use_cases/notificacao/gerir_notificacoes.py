"""Casos de uso para Gestão de Notificações e Alertas (RF05, RF09, RF10)."""
from __future__ import annotations

from uuid import UUID

from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_notificacoes import (
    InterfaceCriarNotificacao,
    InterfaceListarNotificacoes,
    InterfaceMarcarNotificacaoLida,
    InterfaceMarcarTodasLidas,
)
from application.ports.outbound.publicador_eventos import PublicadorEventos
from application.ports.outbound.relogio import Relogio
from application.ports.outbound.repositorio_notificacao import RepositorioNotificacao
from application.ports.outbound.unidade_de_trabalho import UnidadeDeTrabalho
from domain.notificacao.entity import Notificacao, PrioridadeNotificacao, TipoNotificacao
from domain.shared.eventos import EventoDominio
from domain.shared.exceptions import EntidadeNaoEncontradaError


class ListarNotificacoesUseCase(InterfaceListarNotificacoes):
    def __init__(self, repositorio: RepositorioNotificacao) -> None:
        self._repo = repositorio

    async def executar(
        self,
        ator: Ator,
        apenas_nao_lidas: bool = False,
        limite: int = 50,
    ) -> tuple[list[Notificacao], int]:
        papel_str = ator.papel.value if hasattr(ator.papel, "value") else str(ator.papel)
        notificacoes = await self._repo.listar(
            usuario_id=ator.id,
            papel=papel_str,
            apenas_nao_lidas=apenas_nao_lidas,
            limite=limite,
        )
        total_nao_lidas = await self._repo.contar_nao_lidas(usuario_id=ator.id, papel=papel_str)
        return notificacoes, total_nao_lidas


class MarcarNotificacaoLidaUseCase(InterfaceMarcarNotificacaoLida):
    def __init__(
        self,
        repositorio: RepositorioNotificacao,
        relogio: Relogio,
        uow: UnidadeDeTrabalho | None = None,
    ) -> None:
        self._repo = repositorio
        self._relogio = relogio
        self._uow = uow

    async def executar(self, notificacao_id: UUID, ator: Ator) -> Notificacao:
        notif = await self._repo.obter_por_id(notificacao_id)
        if notif is None:
            raise EntidadeNaoEncontradaError("Notificação não encontrada.")
        agora = self._relogio.agora()
        notif.marcar_lida(agora)
        if self._uow:
            async with self._uow:
                salva = await self._repo.salvar(notif)
                await self._uow.commit()
            return salva
        return await self._repo.salvar(notif)


class MarcarTodasNotificacoesLidasUseCase(InterfaceMarcarTodasLidas):
    def __init__(
        self,
        repositorio: RepositorioNotificacao,
        relogio: Relogio,
        uow: UnidadeDeTrabalho | None = None,
    ) -> None:
        self._repo = repositorio
        self._relogio = relogio
        self._uow = uow

    async def executar(self, ator: Ator) -> int:
        agora = self._relogio.agora()
        papel_str = ator.papel.value if hasattr(ator.papel, "value") else str(ator.papel)
        if self._uow:
            async with self._uow:
                res = await self._repo.marcar_todas_lidas(ator.id, papel_str, agora)
                await self._uow.commit()
            return res
        return await self._repo.marcar_todas_lidas(ator.id, papel_str, agora)


class CriarNotificacaoUseCase(InterfaceCriarNotificacao):
    """Caso de uso interno para emitir e publicar notificações no ecossistema."""

    def __init__(
        self,
        repositorio: RepositorioNotificacao,
        publicador: PublicadorEventos,
        relogio: Relogio,
        uow: UnidadeDeTrabalho | None = None,
    ) -> None:
        self._repo = repositorio
        self._publicador = publicador
        self._relogio = relogio
        self._uow = uow

    async def executar(
        self,
        *,
        titulo: str,
        mensagem: str,
        tipo: TipoNotificacao | str = TipoNotificacao.SISTEMA,
        prioridade: PrioridadeNotificacao | str = PrioridadeNotificacao.MEDIA,
        usuario_id: UUID | None = None,
        papel_destinatario: str | None = None,
        departamento_destinatario: str | None = None,
        link: str | None = None,
        metadados: dict | None = None,
    ) -> Notificacao:
        agora = self._relogio.agora()
        notificacao = Notificacao.criar(
            titulo=titulo,
            mensagem=mensagem,
            tipo=tipo,
            prioridade=prioridade,
            usuario_id=usuario_id,
            papel_destinatario=papel_destinatario,
            departamento_destinatario=departamento_destinatario,
            link=link,
            metadados=metadados,
            instante=agora,
        )
        if self._uow:
            async with self._uow:
                salva = await self._repo.salvar(notificacao)
                await self._uow.commit()
        else:
            salva = await self._repo.salvar(notificacao)

        # Transmite via WebSocket
        evento = EventoDominio(
            tipo="NOTIFICACAO_EMITIDA",
            ocorrido_em=agora,
            dados={
                "id": str(salva.id),
                "titulo": salva.titulo,
                "mensagem": salva.mensagem,
                "tipo": salva.tipo.value if hasattr(salva.tipo, "value") else str(salva.tipo),
                "prioridade": salva.prioridade.value if hasattr(salva.prioridade, "value") else str(salva.prioridade),
                "usuario_id": str(salva.usuario_id) if salva.usuario_id else None,
                "papel_destinatario": salva.papel_destinatario,
                "departamento_destinatario": salva.departamento_destinatario,
                "link": salva.link,
                "criada_em": salva.criada_em.isoformat(),
            },
        )
        await self._publicador.publicar(evento)
        return salva
