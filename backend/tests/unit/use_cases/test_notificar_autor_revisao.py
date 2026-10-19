"""Sugestão #2: o agente autor é notificado quando o Delegado valida, devolve ou rejeita (RF04)."""
import pytest

from application.ports.inbound.interface_arquivar_ocorrencia import AutorizacaoDelegadoInput
from application.ports.inbound.interface_revisar_ocorrencia import DecisaoRevisaoInput, ValidarOcorrenciaInput
from application.use_cases.ocorrencia.arquivar_ocorrencia import ArquivarOcorrencia
from application.use_cases.ocorrencia.revisar_ocorrencia import DevolverParaCorrecao, RejeitarOcorrencia, ValidarOcorrencia
from domain.notificacao.entity import PrioridadeNotificacao, TipoNotificacao
from domain.ocorrencia.entity import OrigemOcorrencia
from domain.shared.exceptions import TransicaoInvalidaError
from tests.fakes.atores import AGENTE, DELEGADO
from tests.fakes.repositorio_notificacao_fake import RepositorioNotificacaoFake

JUSTIFICATIVA = "Faltam dados do veículo subtraído."


@pytest.fixture
def notificacoes():
    return RepositorioNotificacaoFake()


async def test_devolucao_notifica_autor_com_justificativa_e_link(registrar, deps, notificacoes, publicador, uow):
    o = await registrar()
    await DevolverParaCorrecao(*deps, notificacoes=notificacoes).executar(
        DELEGADO, DecisaoRevisaoInput(o.ocorrencia_id, JUSTIFICATIVA)
    )
    [n] = notificacoes.itens
    assert n.usuario_id == AGENTE.id and n.tipo == TipoNotificacao.REVISAO_OCORRENCIA
    assert n.prioridade == PrioridadeNotificacao.ALTA
    assert o.numero_protocolo in n.titulo and JUSTIFICATIVA in n.mensagem
    assert n.link == f"/minhas?protocolo={o.numero_protocolo}&ocorrencia={o.ocorrencia_id}"
    assert n.metadados == {"ocorrencia_id": str(o.ocorrencia_id), "numero_protocolo": o.numero_protocolo, "status": "EM_CORRECAO"}
    assert publicador.tipos() == ["OcorrenciaDevolvida", "NOTIFICACAO_EMITIDA"]
    assert publicador.eventos[1].dados["usuario_id"] == str(AGENTE.id)
    assert uow.commits == 2  # registro + decisão (a notificação vai na mesma transação)


@pytest.mark.parametrize(
    ("caso", "entrada", "prioridade"),
    [
        (ValidarOcorrencia, lambda oid: ValidarOcorrenciaInput(oid), PrioridadeNotificacao.BAIXA),
        (RejeitarOcorrencia, lambda oid: DecisaoRevisaoInput(oid, JUSTIFICATIVA), PrioridadeNotificacao.MEDIA),
    ],
)
async def test_validacao_e_rejeicao_notificam_autor(registrar, deps, notificacoes, caso, entrada, prioridade):
    o = await registrar()
    await caso(*deps, notificacoes=notificacoes).executar(DELEGADO, entrada(o.ocorrencia_id))
    [n] = notificacoes.itens
    assert n.usuario_id == AGENTE.id and n.prioridade == prioridade


async def test_validacao_sem_despacho_usa_so_a_natureza(registrar, deps, notificacoes):
    o = await registrar()
    await ValidarOcorrencia(*deps, notificacoes=notificacoes).executar(DELEGADO, ValidarOcorrenciaInput(o.ocorrencia_id))
    assert notificacoes.itens[0].mensagem == "Furto"


async def test_comunicacao_publica_nao_gera_notificacao(registrar, deps, repositorio, notificacoes, publicador):
    o = await registrar()
    repositorio._store[o.ocorrencia_id].origem = OrigemOcorrencia.PUBLICA
    await ValidarOcorrencia(*deps, notificacoes=notificacoes).executar(DELEGADO, ValidarOcorrenciaInput(o.ocorrencia_id))
    assert notificacoes.itens == [] and publicador.tipos() == ["OcorrenciaValidada"]


async def test_decisao_invalida_nao_notifica(registrar, deps, notificacoes):
    o = await registrar()
    uc = ValidarOcorrencia(*deps, notificacoes=notificacoes)
    await uc.executar(DELEGADO, ValidarOcorrenciaInput(o.ocorrencia_id))
    with pytest.raises(TransicaoInvalidaError):
        await uc.executar(DELEGADO, ValidarOcorrenciaInput(o.ocorrencia_id))
    assert len(notificacoes.itens) == 1


async def test_arquivamento_nao_notifica(registrar, deps, notificacoes):
    o = await registrar()
    await ArquivarOcorrencia(*deps, notificacoes=notificacoes).executar(
        DELEGADO, AutorizacaoDelegadoInput(o.ocorrencia_id, "Fato já apurado em outro procedimento.")
    )
    assert notificacoes.itens == []
