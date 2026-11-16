"""Fakes das portas transversais (Relogio, GeradorProtocolo, UnidadeDeTrabalho, Auditoria, Eventos)."""
from datetime import UTC, datetime, timedelta
from uuid import UUID

from application.ports.outbound.gerador_protocolo import GeradorProtocolo, formatar_protocolo
from application.ports.outbound.porta_auditoria import PortaAuditoria
from application.ports.outbound.publicador_eventos import PublicadorEventos
from application.ports.outbound.relogio import Relogio
from application.ports.outbound.unidade_de_trabalho import UnidadeDeTrabalho
from domain.auditoria.contexto import ContextoAuditoria
from domain.auditoria.entity import RegistroAuditoria
from domain.auditoria.evento import EventoAuditoria
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
        self.eventos: list[EventoAuditoria] = []

    async def registrar(self, evento: EventoAuditoria, contexto: ContextoAuditoria) -> None:
        self.eventos.append(evento)
        self.registros.append(evento.para_registro(contexto))

    def semear(self, registro: RegistroAuditoria) -> None:
        """Só para testes: trilha já existente (inclusive com grafias legadas)."""
        self.registros.append(registro)

    async def listar(
        self,
        entidade: str | None = None,
        entidade_id: str | None = None,
        operacao: str | None = None,
        quem: UUID | None = None,
        limit: int = 100,
        de: datetime | None = None,
        ate: datetime | None = None,
        offset: int = 0,
    ) -> list[RegistroAuditoria]:
        # Mesma ordem do adapter SQL: mais recentes primeiro (``quando`` desc).
        itens = sorted(self._filtrar(entidade, entidade_id, operacao, quem, de, ate), key=lambda r: r.quando, reverse=True)
        return itens[offset : offset + limit]

    async def contar(
        self,
        entidade: str | None = None,
        entidade_id: str | None = None,
        operacao: str | None = None,
        quem: UUID | None = None,
        de: datetime | None = None,
        ate: datetime | None = None,
    ) -> int:
        return len(self._filtrar(entidade, entidade_id, operacao, quem, de, ate))

    def _filtrar(
        self,
        entidade: str | None,
        entidade_id: str | None,
        operacao: str | None,
        quem: UUID | None,
        de: datetime | None,
        ate: datetime | None,
    ) -> list[RegistroAuditoria]:
        return [
            r
            for r in self.registros
            if (not entidade or r.entidade == entidade)
            and (not entidade_id or r.entidade_id == entidade_id)
            and (not operacao or r.operacao == operacao)
            and (not quem or r.quem == quem)
            and (de is None or r.quando >= de)
            and (ate is None or r.quando < ate)
        ]

    def operacoes(self) -> list[str]:
        return [r.operacao for r in self.registros]


class PublicadorEventosFake(PublicadorEventos):
    def __init__(self) -> None:
        self.eventos: list[EventoDominio] = []

    async def publicar(self, evento: EventoDominio) -> None:
        self.eventos.append(evento)

    def tipos(self) -> list[str]:
        return [e.tipo for e in self.eventos]
