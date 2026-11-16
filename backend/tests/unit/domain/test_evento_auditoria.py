"""EventoAuditoria: classe base dos eventos de auditoria (Template Method + registro automático)."""
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, ClassVar
from uuid import uuid4

import pytest

from domain.auditoria import evento as modulo_evento
from domain.auditoria.contexto import ContextoAuditoria
from domain.auditoria.evento import EventoAuditoria

AGORA = datetime(2026, 11, 16, 10, 0, tzinfo=UTC)


@pytest.fixture(autouse=True)
def registro_isolado():
    """Subclasses declaradas nos testes não podem vazar para o catálogo real."""
    copia = dict(modulo_evento._EVENTOS_POR_OPERACAO)
    yield
    modulo_evento._EVENTOS_POR_OPERACAO.clear()
    modulo_evento._EVENTOS_POR_OPERACAO.update(copia)


def _declarar_hierarquia():
    @dataclass(frozen=True, kw_only=True)
    class EventoPedido(EventoAuditoria):  # intermediária: sem OPERACAO
        ENTIDADE: ClassVar[str] = "Pedido"
        ENTIDADE_GRAFIAS_LEGADAS: ClassVar[tuple[str, ...]] = ("pedidos",)
        pedido_id: str

        def id_entidade(self) -> str | None:
            return self.pedido_id

    @dataclass(frozen=True, kw_only=True)
    class PedidoAprovado(EventoPedido):
        OPERACAO: ClassVar[str] = "pedido.aprovar"
        GRAFIAS_LEGADAS: ClassVar[tuple[str, ...]] = ("PEDIDO_APROVADO",)
        status_antes: str
        status_depois: str

        def dados_antes(self) -> dict[str, Any] | None:
            return {"status": self.status_antes}

        def dados_depois(self) -> dict[str, Any] | None:
            return {"status": self.status_depois}

    return EventoPedido, PedidoAprovado


def test_subclasse_concreta_entra_no_catalogo_e_a_intermediaria_nao():
    _, aprovado = _declarar_hierarquia()

    assert ("pedido.aprovar", "Pedido") in EventoAuditoria.catalogo()
    assert EventoAuditoria.classe_de("pedido.aprovar") is aprovado
    assert all(entidade != "Pedido" or op == "pedido.aprovar" for op, entidade in EventoAuditoria.catalogo())


def test_classe_intermediaria_e_abstrata():
    intermediaria, _ = _declarar_hierarquia()

    with pytest.raises(TypeError):
        intermediaria(pedido_id="1")


def test_para_registro_monta_o_registro_com_contexto_e_payload():
    _, aprovado = _declarar_hierarquia()
    quem = uuid4()

    registro = aprovado(pedido_id="42", status_antes="ABERTO", status_depois="APROVADO").para_registro(
        ContextoAuditoria(quem=quem, quando=AGORA, ip="10.0.0.1")
    )

    assert (registro.quem, registro.quando, registro.ip) == (quem, AGORA, "10.0.0.1")
    assert (registro.operacao, registro.entidade, registro.entidade_id) == ("pedido.aprovar", "Pedido", "42")
    assert registro.dados_antes == {"status": "ABERTO"} and registro.dados_depois == {"status": "APROVADO"}


def test_grafias_incluem_as_legadas():
    _declarar_hierarquia()

    assert EventoAuditoria.grafias("pedido.aprovar") == ("pedido.aprovar", "PEDIDO_APROVADO")
    assert EventoAuditoria.grafias_da_entidade("Pedido") == ("Pedido", "pedidos")
    assert EventoAuditoria.grafias("inexistente.acao") == ("inexistente.acao",)


@pytest.mark.parametrize("operacao", ["PedidoAprovado", "pedido", "pedido.Aprovar", "pedido.aprovar.agora"])
def test_operacao_fora_do_formato_dominio_acao_e_recusada(operacao):
    with pytest.raises(TypeError, match="dominio.acao"):

        @dataclass(frozen=True, kw_only=True)
        class Invalido(EventoAuditoria):
            OPERACAO: ClassVar[str] = operacao
            ENTIDADE: ClassVar[str] = "Pedido"


def test_operacao_repetida_em_outra_classe_e_recusada():
    _declarar_hierarquia()

    with pytest.raises(TypeError, match="já pertence"):

        @dataclass(frozen=True, kw_only=True)
        class OutroAprovado(EventoAuditoria):
            OPERACAO: ClassVar[str] = "pedido.aprovar"
            ENTIDADE: ClassVar[str] = "Pedido"


def test_acao_sem_entidade_e_recusada():
    with pytest.raises(TypeError, match="ENTIDADE"):

        @dataclass(frozen=True, kw_only=True)
        class SemEntidade(EventoAuditoria):
            OPERACAO: ClassVar[str] = "pedido.cancelar"
