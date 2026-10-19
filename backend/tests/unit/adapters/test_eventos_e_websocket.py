"""PublicadorEventosEmMemoria (fan-out isolado) e GerenciadorConexoes (RF02 / RNF01, DEC-06)."""
import json
from datetime import UTC, datetime, timedelta

import pytest

from adapters.inbound.websocket.audiencia import pode_receber
from adapters.inbound.websocket.gerenciador_conexoes import GerenciadorConexoes, Sessao
from adapters.outbound.eventos.publicador_em_memoria import PublicadorEventosEmMemoria
from domain.shared.eventos import EventoDominio
from tests.fakes.atores import AGENTE, DELEGADO, OPERADOR
from tests.fakes.portas_fake import RelogioFake

AGORA = datetime(2026, 9, 13, tzinfo=UTC)
EVENTO = EventoDominio(tipo="Teste", ocorrido_em=AGORA, dados={"x": 1})
POSICAO = EventoDominio(tipo="PosicaoAtualizada", ocorrido_em=AGORA, dados={"viatura_id": "v1"})


def _sessao(ator=OPERADOR, expira_em=AGORA + timedelta(hours=1)) -> Sessao:
    return Sessao(ator=ator, expira_em=expira_em)


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

    async def accept(self, subprotocol=None):
        self.aceito, self.subprotocolo = True, subprotocol

    async def send_text(self, m):
        if self.falha:
            raise RuntimeError("closed")
        self.msgs.append(m)

    async def close(self, code=1000, reason=""):
        self.fechado = code


async def test_gerenciador_transmite_e_descarta_conexoes_mortas():
    g = GerenciadorConexoes(RelogioFake(AGORA))
    a, b = _WsFake(), _WsFake(falha=True)
    await g.conectar(a, _sessao())
    await g.conectar(b, _sessao())
    assert g.total == 2 and a.aceito
    await g.transmitir(POSICAO)
    assert g.total == 1 and json.loads(a.msgs[0]) == {
        "tipo": "PosicaoAtualizada", "ocorrido_em": "2026-09-13T00:00:00+00:00", "dados": {"viatura_id": "v1"}
    }
    g.desconectar(a)
    await g.transmitir(POSICAO)  # sem conexões: no-op
    assert g.total == 0


async def test_falha_no_meio_descarta_o_socket_certo():
    """Regressão: o zip com a lista recriada após o await desalinhava e descartava o socket errado."""
    g = GerenciadorConexoes(RelogioFake(AGORA))
    socks = [_WsFake(), _WsFake(falha=True), _WsFake()]
    for ws in socks:
        await g.conectar(ws, _sessao())
    await g.transmitir(POSICAO)
    assert g.total == 2 and socks[0].msgs and socks[2].msgs


async def test_tipo_de_evento_desconhecido_nao_e_entregue():
    g = GerenciadorConexoes(RelogioFake(AGORA))
    a = _WsFake()
    await g.conectar(a, _sessao())
    await g.transmitir(EVENTO)
    assert a.msgs == []


async def test_notificacao_pessoal_so_chega_ao_destinatario():
    g = GerenciadorConexoes(RelogioFake(AGORA))
    dono, outro = _WsFake(), _WsFake()
    await g.conectar(dono, _sessao(AGENTE))
    await g.conectar(outro, _sessao(DELEGADO))
    await g.transmitir(EventoDominio("NOTIFICACAO_EMITIDA", AGORA, {"usuario_id": str(AGENTE.id)}))
    assert len(dono.msgs) == 1 and outro.msgs == []


async def test_sessao_expirada_e_fechada_com_1008_e_nao_recebe():
    g = GerenciadorConexoes(RelogioFake(AGORA))
    vencida = _WsFake()
    await g.conectar(vencida, _sessao(expira_em=AGORA - timedelta(seconds=1)))
    await g.transmitir(POSICAO)
    assert vencida.msgs == [] and vencida.fechado == 1008 and g.total == 0


@pytest.mark.parametrize(
    ("evento", "ator", "esperado"),
    [
        (EventoDominio("NOTIFICACAO_EMITIDA", AGORA, {"papel_destinatario": "DELEGADO"}), DELEGADO, True),
        (EventoDominio("NOTIFICACAO_EMITIDA", AGORA, {"papel_destinatario": "DELEGADO"}), AGENTE, False),
        (EventoDominio("NOTIFICACAO_EMITIDA", AGORA, {}), AGENTE, True),
        (EventoDominio("ALERTA_CRITICIDADE", AGORA, {"dados": {"papel_destinatario": "SUPERVISOR"}}), OPERADOR, False),
        (EventoDominio("ALERTA_CRITICIDADE", AGORA, {"dados": {}}), OPERADOR, True),
        (EventoDominio("MEDIDA_VENCIMENTO_ALERTA", AGORA, {}), AGENTE, True),
        (EventoDominio("COMUNICACAO_INTERAGENCIAS_CRIADA", AGORA, {}), AGENTE, False),
        (EventoDominio("COMUNICACAO_INTERAGENCIAS_CRIADA", AGORA, {}), DELEGADO, True),
    ],
)
def test_audiencia_por_tipo_de_evento(evento, ator, esperado):
    assert pode_receber(evento, ator) is esperado
