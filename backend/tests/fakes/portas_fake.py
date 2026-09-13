"""Fakes das portas transversais (Relogio, GeradorProtocolo, UnidadeDeTrabalho, Auditoria, Eventos)."""
from datetime import UTC, datetime, timedelta

from application.ports.outbound.gerador_protocolo import GeradorProtocolo, formatar_protocolo
from application.ports.outbound.porta_auditoria import PortaAuditoria
from application.ports.outbound.publicador_eventos import PublicadorEventos
from application.ports.outbound.relogio import Relogio
from application.ports.outbound.unidade_de_trabalho import UnidadeDeTrabalho
from domain.auditoria.entity import RegistroAuditoria
from domain.shared.eventos import EventoDominio


class RelogioFake(Relogio):
    def __init__(self, instante: datetime | None = None) -> None:
        self.instante = instante or datetime(2026, 9, 13, 12, 0, tzinfo=UTC)

    def agora(self) -> datetime:
        return self.instante

    def avancar(self, **delta: int) -> None:
        self.instante += timedelta(**delta)


class GeradorProtocoloFake(GeradorProtocolo):
    def __init__(self) -> None:
        self._contadores: dict[int, int] = {}

    async def proximo(self, ano: int) -> str:
        self._contadores[ano] = self._contadores.get(ano, 0) + 1
        return formatar_protocolo(ano, self._contadores[ano])


class UnidadeDeTrabalhoFake(UnidadeDeTrabalho):
    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        self.rollbacks += 1


class AuditoriaFake(PortaAuditoria):
    def __init__(self) -> None:
        self.registros: list[RegistroAuditoria] = []

    async def registrar(self, registro: RegistroAuditoria) -> None:
        self.registros.append(registro)

    async def listar(self, entidade=None, entidade_id=None, limit=100):
        itens = self.registros
        if entidade:
            itens = [r for r in itens if r.entidade == entidade]
        if entidade_id:
            itens = [r for r in itens if r.entidade_id == entidade_id]
        return itens[:limit]

    def operacoes(self) -> list[str]:
        return [r.operacao for r in self.registros]


class PublicadorEventosFake(PublicadorEventos):
    def __init__(self) -> None:
        self.eventos: list[EventoDominio] = []

    async def publicar(self, evento: EventoDominio) -> None:
        self.eventos.append(evento)

    def tipos(self) -> list[str]:
        return [e.tipo for e in self.eventos]
