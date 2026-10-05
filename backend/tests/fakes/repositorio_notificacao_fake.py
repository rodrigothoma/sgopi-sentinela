"""Repositório de notificações em memória (só o necessário aos casos de uso que emitem avisos)."""
from datetime import datetime
from uuid import UUID

from application.ports.outbound.repositorio_notificacao import RepositorioNotificacao
from domain.notificacao.entity import Notificacao


class RepositorioNotificacaoFake(RepositorioNotificacao):
    def __init__(self) -> None:
        self.itens: list[Notificacao] = []
        self.leituras: set[tuple[UUID, UUID]] = set()

    async def salvar(self, notificacao: Notificacao) -> Notificacao:
        self.itens.append(notificacao)
        return notificacao

    async def obter_por_id(self, notificacao_id: UUID) -> Notificacao | None:
        return next((n for n in self.itens if n.id == notificacao_id), None)

    async def listar(self, usuario_id=None, papel=None, apenas_nao_lidas=False, limite=50, offset=0) -> list[Notificacao]:
        visiveis = [n for n in self.itens if usuario_id is None or n.destinada_a(usuario_id, papel or "")]
        if apenas_nao_lidas:
            visiveis = [n for n in visiveis if (n.id, usuario_id) not in self.leituras]
        return visiveis[offset : offset + limite]

    async def contar_nao_lidas(self, usuario_id=None, papel=None) -> int:
        return len(await self.listar(usuario_id, papel, apenas_nao_lidas=True, limite=len(self.itens)))

    async def registrar_leitura(self, notificacao_id: UUID, usuario_id: UUID, instante: datetime) -> None:
        self.leituras.add((notificacao_id, usuario_id))

    async def marcar_todas_lidas(self, usuario_id, papel, instante) -> int:
        pendentes = await self.listar(usuario_id, papel, apenas_nao_lidas=True, limite=len(self.itens))
        for n in pendentes:
            self.leituras.add((n.id, usuario_id))
        return len(pendentes)
