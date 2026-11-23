"""Fakes das portas transversais (Relogio, GeradorNumeroSequencial, UnidadeDeTrabalho, Auditoria, Eventos)."""
from datetime import UTC, datetime, timedelta
from uuid import UUID

from application.ports.outbound.gerador_numero_sequencial import (
    GeradorNumeroSequencial,
    TipoDocumentoSequencial,
    formatar_numero_sequencial,
)
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


class GeradorNumeroSequencialFake(GeradorNumeroSequencial):
    """Contador em memória por (tipo, ano), com o mesmo formato do adaptador SQL.

    ``numero_fixo`` devolve sempre o mesmo número (simula colisão); ``falhar`` simula sequência indisponível.
    """

    def __init__(self, *, numero_fixo: str | None = None, falhar: bool = False) -> None:
        self._contadores: dict[tuple[TipoDocumentoSequencial, int], int] = {}
        self._numero_fixo = numero_fixo
        self.falhar = falhar

    async def proximo(self, tipo: TipoDocumentoSequencial, ano: int) -> str:
        if self.falhar:
            raise RuntimeError(f"falha simulada ao gerar número de {tipo}")
        if self._numero_fixo is not None:
            return self._numero_fixo
        chave = (tipo, ano)
        self._contadores[chave] = self._contadores.get(chave, 0) + 1
        return formatar_numero_sequencial(tipo, ano, self._contadores[chave])


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
