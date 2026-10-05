"""VincularOcorrenciasInquerito e BuscarConexoesOcorrencia (RF06 / UC06) — antes com 22% e 43% de cobertura (N10)."""
from uuid import uuid4

import pytest

from application.ports.inbound.interface_gerir_inqueritos import VincularOcorrenciasInput
from application.ports.inbound.interface_registrar_ocorrencia_policial import EnvolvidoInputDTO
from application.ports.inbound.interface_revisar_ocorrencia import ValidarOcorrenciaInput
from application.ports.outbound.repositorio_inquerito import RepositorioInquerito
from application.use_cases.inquerito.buscar_conexoes import BuscarConexoesOcorrencia
from application.use_cases.inquerito.vincular_ocorrencias import VincularOcorrenciasInquerito
from application.use_cases.ocorrencia.revisar_ocorrencia import ValidarOcorrencia
from domain.inquerito.entity import Inquerito
from domain.shared.exceptions import AcessoNegadoError, ConflitoError, EntidadeNaoEncontradaError
from tests.fakes.atores import AGENTE, DELEGADO
from tests.unit.use_cases.conftest import AGORA


class RepositorioInqueritoFake(RepositorioInquerito):
    def __init__(self) -> None:
        self.itens: dict = {}

    async def salvar(self, inquerito):
        self.itens[inquerito.id] = inquerito

    async def buscar_por_id(self, inquerito_id):
        return self.itens.get(inquerito_id)

    async def buscar_por_numero(self, numero):
        return next((i for i in self.itens.values() if i.numero == numero), None)

    async def listar(self, status=None, limit=50, offset=0):
        return list(self.itens.values()), len(self.itens)


SUSPEITO = EnvolvidoInputDTO(nome="João Silva", tipo="SUSPEITO", documento="111.222.333-44")
VITIMA = EnvolvidoInputDTO(nome="Maria", tipo="VITIMA")


@pytest.fixture
def inqueritos():
    return RepositorioInqueritoFake()


@pytest.fixture
async def inquerito(inqueritos):
    i = Inquerito.instaurar(numero="IP-2026-000001", ementa="Série de furtos no centro da cidade", delegado_id=DELEGADO.id, instante=AGORA)
    await inqueritos.salvar(i)
    return i


@pytest.fixture
def vincular(inqueritos, repositorio, relogio, uow, auditoria):
    return VincularOcorrenciasInquerito(inqueritos, repositorio, relogio, uow, auditoria)


@pytest.fixture
def validar(deps):
    async def _validar(ocorrencia_id):
        await ValidarOcorrencia(*deps).executar(DELEGADO, ValidarOcorrenciaInput(ocorrencia_id))
        return ocorrencia_id

    return _validar


async def test_vincula_ocorrencias_validadas_e_audita(vincular, inquerito, registrar, validar, repositorio, auditoria):
    a = await validar((await registrar()).ocorrencia_id)
    b = await validar((await registrar()).ocorrencia_id)
    out = await vincular.executar(DELEGADO, VincularOcorrenciasInput(inquerito_id=inquerito.id, ocorrencias_ids=[a, b]))
    assert {o.id for o in out.ocorrencias} == {a, b}
    assert (await repositorio.buscar_por_id(a)).inquerito_id == inquerito.id
    assert auditoria.registros[-1].operacao == "inquerito.vincular_ocorrencias"
    assert auditoria.registros[-1].dados_depois["total_vinculadas"] == 2


async def test_vincular_e_idempotente_no_mesmo_inquerito(vincular, inquerito, registrar, validar):
    a = await validar((await registrar()).ocorrencia_id)
    dados = VincularOcorrenciasInput(inquerito_id=inquerito.id, ocorrencias_ids=[a])
    await vincular.executar(DELEGADO, dados)
    out = await vincular.executar(DELEGADO, dados)
    assert [o.id for o in out.ocorrencias] == [a]


async def test_so_delegado_vincula(vincular, inquerito):
    with pytest.raises(AcessoNegadoError):
        await vincular.executar(AGENTE, VincularOcorrenciasInput(inquerito_id=inquerito.id, ocorrencias_ids=[]))


async def test_inquerito_ou_ocorrencia_inexistente(vincular, inquerito):
    with pytest.raises(EntidadeNaoEncontradaError):
        await vincular.executar(DELEGADO, VincularOcorrenciasInput(inquerito_id=uuid4(), ocorrencias_ids=[]))
    with pytest.raises(EntidadeNaoEncontradaError):
        await vincular.executar(DELEGADO, VincularOcorrenciasInput(inquerito_id=inquerito.id, ocorrencias_ids=[uuid4()]))


async def test_recusa_ocorrencia_nao_validada(vincular, inquerito, registrar):
    pendente = (await registrar()).ocorrencia_id
    with pytest.raises(ConflitoError) as exc:
        await vincular.executar(DELEGADO, VincularOcorrenciasInput(inquerito_id=inquerito.id, ocorrencias_ids=[pendente]))
    assert exc.value.chave == "inquerito.ocorrencia_nao_validada"


async def test_recusa_ocorrencia_de_outro_inquerito(vincular, inquerito, inqueritos, registrar, validar):
    a = await validar((await registrar()).ocorrencia_id)
    await vincular.executar(DELEGADO, VincularOcorrenciasInput(inquerito_id=inquerito.id, ocorrencias_ids=[a]))
    outro = Inquerito.instaurar(numero="IP-2026-000002", ementa="Outro procedimento investigativo", delegado_id=DELEGADO.id, instante=AGORA)
    await inqueritos.salvar(outro)
    with pytest.raises(ConflitoError) as exc:
        await vincular.executar(DELEGADO, VincularOcorrenciasInput(inquerito_id=outro.id, ocorrencias_ids=[a]))
    assert exc.value.chave == "inquerito.ocorrencia_ja_vinculada"


async def test_conexoes_pontuam_suspeito_natureza_e_proximidade(registrar, validar, repositorio):
    pivo = await validar((await registrar(envolvidos=(VITIMA, SUSPEITO))).ocorrencia_id)
    mesmo_doc = await validar((await registrar(envolvidos=(VITIMA, SUSPEITO))).ocorrencia_id)
    so_nome = await validar(
        (await registrar(natureza="Roubo", latitude=-30.5, longitude=-56.5,
                         envolvidos=(EnvolvidoInputDTO(nome="  joão silva ", tipo="SUSPEITO"),))).ocorrencia_id
    )
    sem_relacao = await validar(
        (await registrar(natureza="Ameaça", latitude=-30.5, longitude=-56.5, envolvidos=(VITIMA,))).ocorrencia_id
    )
    await registrar()  # não validada: nunca é candidata

    sugestoes = await BuscarConexoesOcorrencia(repositorio).executar(DELEGADO, pivo)

    assert [s.ocorrencia_id for s in sugestoes] == [mesmo_doc, so_nome]
    assert sugestoes[0].pontuacao_relevancia == 100 + 30 + 40
    assert "documento" in sugestoes[0].motivo_conexao and "Proximidade" in sugestoes[0].motivo_conexao
    assert sugestoes[1].pontuacao_relevancia == 70 and "João Silva" in sugestoes[1].motivo_conexao
    assert sem_relacao not in [s.ocorrencia_id for s in sugestoes]


async def test_conexoes_ignoram_ocorrencias_ja_em_inquerito(registrar, validar, repositorio):
    pivo = await validar((await registrar()).ocorrencia_id)
    vinculada = await validar((await registrar()).ocorrencia_id)
    o = await repositorio.buscar_por_id(vinculada)
    o.vincular_inquerito(uuid4())
    await repositorio.salvar(o)
    assert await BuscarConexoesOcorrencia(repositorio).executar(DELEGADO, pivo) == []


async def test_conexoes_pivo_inexistente(repositorio):
    with pytest.raises(EntidadeNaoEncontradaError):
        await BuscarConexoesOcorrencia(repositorio).executar(DELEGADO, uuid4())
