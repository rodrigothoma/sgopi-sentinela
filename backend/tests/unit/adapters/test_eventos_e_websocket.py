"""PublicadorEventosEmMemoria (fan-out isolado) e GerenciadorConexoes (RF02 / RNF01, DEC-06)."""
import json
from datetime import UTC, datetime

from adapters.inbound.websocket.gerenciador_conexoes import GerenciadorConexoes
from adapters.outbound.eventos.publicador_em_memoria import PublicadorEventosEmMemoria
from domain.shared.eventos import EventoDominio

EVENTO = EventoDominio(tipo="Teste", ocorrido_em=datetime(2026, 9, 13, tzinfo=UTC), dados={"x": 1})


async def test_publicador_entrega_a_todos_e_isola_falhas():
    pub = PublicadorEventosEmMemoria()
    recebidos = []

    async def ok(e):
        recebidos.append(e.tipo)

    async def quebrado(e):
        raise RuntimeError("boom")

    pub.assinar(quebrado)
    pub.assinar(ok)
    await pub.publicar(EVENTO)
    assert recebidos == ["Teste"]
    pub.cancelar(ok)
    await pub.publicar(EVENTO)
    assert recebidos == ["Teste"]


class _WsFake:
    def __init__(self, falha=False):
        self.msgs, self.falha, self.aceito = [], falha, False

    async def accept(self):
        self.aceito = True

    async def send_text(self, m):
        if self.falha:
            raise RuntimeError("closed")
        self.msgs.append(m)


async def test_gerenciador_transmite_e_descarta_conexoes_mortas():
    g = GerenciadorConexoes()
    a, b = _WsFake(), _WsFake(falha=True)
    await g.conectar(a)
    await g.conectar(b)
    assert g.total == 2 and a.aceito
    await g.transmitir(EVENTO)
    assert g.total == 1 and json.loads(a.msgs[0]) == {"tipo": "Teste", "ocorrido_em": "2026-09-13T00:00:00+00:00", "dados": {"x": 1}}
    g.desconectar(a)
    await g.transmitir(EVENTO)  # sem conexões: no-op
    assert g.total == 0
