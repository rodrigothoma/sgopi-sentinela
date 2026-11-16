"""Edição e retirada da frota: autorização, auditoria, eventos e preservação de referências."""
from uuid import uuid4

import pytest

from application.ports.inbound.interface_gerir_viaturas import EditarViaturaInput, ExcluirViaturaInput
from application.use_cases.viatura.manter_cadastro import EditarViatura, ExcluirViatura
from domain.despacho.entity import OrdemDeDespacho
from domain.shared.exceptions import AcessoNegadoError, ConflitoError, EntidadeNaoEncontradaError
from domain.viatura.entity import Viatura
from tests.fakes.atores import AGENTE, OPERADOR
from tests.fakes.despacho_fake import RepositorioOrdemDespachoFake
from tests.fakes.portas_fake import AuditoriaFake, PublicadorEventosFake, RelogioFake, UnidadeDeTrabalhoFake
from tests.fakes.repositorio_viatura_fake import RepositorioViaturaFake
from tests.unit.use_cases.conftest import AGORA


@pytest.fixture
def deps() -> tuple:
    return RepositorioViaturaFake(), RepositorioOrdemDespachoFake(), UnidadeDeTrabalhoFake(), RelogioFake(AGORA), AuditoriaFake(), PublicadorEventosFake()


async def test_edicao_preserva_telemetria_audita_antes_depois_e_publica(deps: tuple) -> None:
    repo, _, uow, relogio, auditoria, eventos = deps
    v = Viatura("VTR-01", "ABC1234")
    await repo.salvar(v)
    uc = EditarViatura(repo, uow, relogio, auditoria, eventos, 60)
    out = await uc.executar(OPERADOR, EditarViaturaInput(v.id, "VTR-01", "DEF5678", "Ana", 1))
    assert out.id == v.id and out.responsavel == "Ana" and out.versao == 2
    assert out.situacao == "DISPONIVEL" and out.latitude is None
    assert auditoria.operacoes() == ["viatura.editar"] and uow.commits == 1
    assert auditoria.registros[0].dados_antes["placa"] == "ABC1234"
    assert auditoria.registros[0].dados_depois["responsavel"] == "Ana"
    assert eventos.tipos() == ["ViaturaCadastroAlterado"]


async def test_exclusao_logica_preserva_busca_historica_e_audita(deps: tuple) -> None:
    repo, ordens, uow, relogio, auditoria, eventos = deps
    v = Viatura("VTR-01", "ABC1234", responsavel="Ana")
    await repo.salvar(v)
    await ExcluirViatura(repo, ordens, uow, relogio, auditoria, eventos).executar(OPERADOR, ExcluirViaturaInput(v.id, 1))
    assert await repo.listar() == []
    salvo = await repo.buscar_por_id(v.id)
    assert salvo is not None and not salvo.ativo and salvo.responsavel == "Ana"
    assert auditoria.operacoes() == ["viatura.excluir"] and uow.commits == 1
    assert eventos.tipos() == ["ViaturaExcluida"]
    with pytest.raises(EntidadeNaoEncontradaError):
        await EditarViatura(repo, uow, relogio, auditoria, eventos, 60).executar(OPERADOR, EditarViaturaInput(v.id, "A", "B", None, 2))


async def test_ordem_ativa_impede_exclusao_sem_evento_ou_commit(deps: tuple) -> None:
    repo, ordens, uow, relogio, auditoria, eventos = deps
    v = Viatura("VTR-01", "ABC1234")
    await repo.salvar(v)
    await ordens.salvar(OrdemDeDespacho("OD-1", uuid4(), v.id, OPERADOR.id, AGORA))
    with pytest.raises(ConflitoError) as erro:
        await ExcluirViatura(repo, ordens, uow, relogio, auditoria, eventos).executar(OPERADOR, ExcluirViaturaInput(v.id, 1))
    assert erro.value.chave == "viatura.exclusao_em_atendimento"
    assert (await repo.buscar_por_id(v.id)).ativo
    assert uow.commits == 0 and eventos.tipos() == [] and auditoria.operacoes() == []


async def test_agente_nao_pode_editar_ou_excluir(deps: tuple) -> None:
    repo, ordens, uow, relogio, auditoria, eventos = deps
    with pytest.raises(AcessoNegadoError):
        await EditarViatura(repo, uow, relogio, auditoria, eventos, 60).executar(AGENTE, EditarViaturaInput(uuid4(), "A", "B", None, 1))
    with pytest.raises(AcessoNegadoError):
        await ExcluirViatura(repo, ordens, uow, relogio, auditoria, eventos).executar(AGENTE, ExcluirViaturaInput(uuid4(), 1))
    assert uow.commits == 0 and eventos.tipos() == []
