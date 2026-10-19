from datetime import datetime
from uuid import uuid4

import pytest

from application.ports.inbound.ator import Ator
from application.ports.outbound.publicador_eventos import PublicadorEventos
from application.ports.outbound.relogio import Relogio
from application.ports.outbound.repositorio_notificacao import RepositorioNotificacao
from application.use_cases.notificacao.gerir_notificacoes import (
    CriarNotificacaoUseCase,
    ListarNotificacoesUseCase,
    MarcarNotificacaoLidaUseCase,
    MarcarTodasNotificacoesLidasUseCase,
)
from domain.notificacao.entity import Notificacao, PrioridadeNotificacao, TipoNotificacao
from domain.usuario.entity import Papel


class RepositorioNotificacaoEmMemoria(RepositorioNotificacao):
    def __init__(self) -> None:
        self.itens: dict[str, Notificacao] = {}
        self.leituras: set[tuple[str, str]] = set()

    async def salvar(self, notificacao: Notificacao) -> Notificacao:
        self.itens[str(notificacao.id)] = notificacao
        return notificacao

    async def obter_por_id(self, notificacao_id):
        return self.itens.get(str(notificacao_id))

    async def registrar_leitura(self, notificacao_id, usuario_id, instante):
        self.leituras.add((str(notificacao_id), str(usuario_id)))

    async def listar(self, usuario_id=None, papel=None, apenas_nao_lidas=False, limite=50, offset=0):
        res = list(self.itens.values())
        if apenas_nao_lidas:
            res = [n for n in res if not n.lida]
        return res[:limite]

    async def contar_nao_lidas(self, usuario_id=None, papel=None) -> int:
        return sum(1 for n in self.itens.values() if not n.lida)

    async def marcar_todas_lidas(self, usuario_id, papel, instante) -> int:
        count = 0
        for n in self.itens.values():
            if not n.lida:
                n.marcar_lida(instante)
                count += 1
        return count


class PublicadorFake(PublicadorEventos):
    def __init__(self) -> None:
        self.eventos = []

    async def publicar(self, evento) -> None:
        self.eventos.append(evento)


class RelogioFixo(Relogio):
    def agora(self) -> datetime:
        return datetime(2026, 10, 3, 12, 0, 0)


@pytest.mark.asyncio
async def test_fluxo_completo_notificacoes():
    repo = RepositorioNotificacaoEmMemoria()
    pub = PublicadorFake()
    rel = RelogioFixo()
    ator = Ator(id=uuid4(), papel=Papel.DELEGADO, login="dr_silva")

    uc_criar = CriarNotificacaoUseCase(repo, pub, rel)
    uc_listar = ListarNotificacoesUseCase(repo)
    uc_marcar = MarcarNotificacaoLidaUseCase(repo, rel)
    uc_marcar_todas = MarcarTodasNotificacoesLidasUseCase(repo, rel)

    # 1. Cria notificação
    n1 = await uc_criar.executar(
        titulo="Nova Ocorrência",
        mensagem="Ocorrência registrada no plantão policial.",
        tipo=TipoNotificacao.NOVA_OCORRENCIA,
        prioridade=PrioridadeNotificacao.ALTA,
        papel_destinatario="DELEGADO",
    )
    assert len(pub.eventos) == 1
    assert pub.eventos[0].tipo == "NOTIFICACAO_EMITIDA"

    # 2. Lista e conta não lidas
    lista, nao_lidas = await uc_listar.executar(ator)
    assert len(lista) == 1
    assert nao_lidas == 1

    # 3. Marca individual como lida
    n1_lida = await uc_marcar.executar(n1.id, ator)
    assert n1_lida.lida is True

    # 4. Cria mais duas notificações e marca todas como lidas
    await uc_criar.executar(titulo="Alerta 2", mensagem="Segundo alerta operacional")
    await uc_criar.executar(titulo="Alerta 3", mensagem="Terceiro alerta operacional")

    _, nao_lidas2 = await uc_listar.executar(ator)
    assert nao_lidas2 == 2

    marcadas = await uc_marcar_todas.executar(ator)
    assert marcadas == 2

    _, nao_lidas3 = await uc_listar.executar(ator)
    assert nao_lidas3 == 0
