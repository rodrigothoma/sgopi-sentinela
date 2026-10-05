"""
Testes unitários dos casos de uso do canal público (RF01 — Delegacia Online):
RegistrarOcorrenciaPublica e ConsultarOcorrenciaPublica. Fakes de todas as portas.
"""
from datetime import UTC, datetime, timedelta

import pytest

from application.ports.inbound.interface_registrar_ocorrencia_policial import EnvolvidoInputDTO, RegistrarOcorrenciaInput
from application.ports.inbound.interface_registrar_ocorrencia_publica import RegistrarOcorrenciaPublicaInput
from application.use_cases.ocorrencia.consultar_ocorrencia_publica import ConsultarOcorrenciaPublica
from application.use_cases.ocorrencia.registrar_ocorrencia_policial import RegistrarOcorrenciaPolicial
from application.use_cases.ocorrencia.registrar_ocorrencia_publica import RegistrarOcorrenciaPublica
from domain.ocorrencia.entity import OrigemOcorrencia, TipoEnvolvido
from domain.ocorrencia.status import StatusOcorrencia
from domain.shared.exceptions import AcessoNegadoError, EntidadeNaoEncontradaError, TransicaoInvalidaError, ValorInvalidoError
from domain.usuario.entity import LOGIN_SISTEMA_CIDADAO, Papel
from tests.fakes.atores import AGENTE, DELEGADO
from tests.fakes.auth_fake import RepositorioUsuarioFake
from tests.fakes.portas_fake import AuditoriaFake, GeradorProtocoloFake, RelogioFake, UnidadeDeTrabalhoFake
from tests.fakes.repositorio_ocorrencia_fake import RepositorioOcorrenciaFake

AGORA = datetime(2026, 9, 13, 12, 0, tzinfo=UTC)


@pytest.fixture
def repositorio():
    return RepositorioOcorrenciaFake()


@pytest.fixture
def usuarios():
    return RepositorioUsuarioFake()


@pytest.fixture
def registro_policial(repositorio):
    return RegistrarOcorrenciaPolicial(repositorio, UnidadeDeTrabalhoFake(), RelogioFake(AGORA), GeradorProtocoloFake(), AuditoriaFake())


@pytest.fixture
def registrar(registro_policial, usuarios):
    return RegistrarOcorrenciaPublica(registro_policial, usuarios, UnidadeDeTrabalhoFake())


@pytest.fixture
def consultar(repositorio):
    return ConsultarOcorrenciaPublica(repositorio)


def _input(**kwargs) -> RegistrarOcorrenciaPublicaInput:
    dados = dict(
        nome_solicitante=" Carlos Alberto ",
        documento="529.982.247-25",
        email=" carlos@exemplo.com ",
        telefone="(55) 99876-5432",
        declaracao_maioridade=True,
        natureza="Furto",
        descricao="  Bicicleta furtada no bicicletário da praça central.  ",
        localizacao="Praça Getúlio Vargas",
        latitude=-29.78,
        longitude=-55.79,
        data_hora_fato=AGORA - timedelta(hours=1),
    )
    dados.update(kwargs)
    return RegistrarOcorrenciaPublicaInput(**dados)


async def test_registra_cidadao_como_comunicante_com_dados_normalizados(registrar, repositorio):
    out = await registrar.executar(_input())
    ocorrencia = await repositorio.buscar_por_id(out.ocorrencia_id)
    assert out.status == StatusOcorrencia.AGUARDANDO_REVISAO.value
    assert ocorrencia.descricao == "Bicicleta furtada no bicicletário da praça central."
    (comunicante,) = ocorrencia.envolvidos
    assert comunicante.tipo == TipoEnvolvido.COMUNICANTE
    assert (comunicante.nome, comunicante.email) == ("Carlos Alberto", "carlos@exemplo.com")


async def test_recusa_sem_declaracao_de_maioridade(registrar):
    with pytest.raises(ValorInvalidoError) as exc:
        await registrar.executar(_input(declaracao_maioridade=False))
    assert exc.value.chave == "ocorrencia.declaracao_maioridade_ausente"


async def test_recusa_cpf_com_digitos_verificadores_invalidos(registrar):
    with pytest.raises(ValorInvalidoError) as exc:
        await registrar.executar(_input(documento="111.111.111-11"))
    assert exc.value.chave == "envolvido.cpf_comunicante_invalido"


async def test_registro_e_autorado_pelo_usuario_de_sistema_cidadao_e_nao_por_agente(registrar, repositorio, usuarios):
    out = await registrar.executar(_input())
    ocorrencia = await repositorio.buscar_por_id(out.ocorrencia_id)
    sistema = await usuarios.buscar_por_login(LOGIN_SISTEMA_CIDADAO)
    assert sistema.papel == Papel.CIDADAO and sistema.ativo is False
    assert ocorrencia.agente_policial_id == sistema.id
    assert ocorrencia.origem == OrigemOcorrencia.PUBLICA


async def test_reutiliza_o_usuario_de_sistema_existente(registrar, usuarios):
    await registrar.executar(_input())
    await registrar.executar(_input())
    assert len(await usuarios.listar()) == 1


async def test_guarda_so_o_hash_do_codigo_de_acompanhamento(registrar, repositorio):
    out = await registrar.executar(_input())
    ocorrencia = await repositorio.buscar_por_id(out.ocorrencia_id)
    assert len(out.codigo_acompanhamento) == 10
    assert ocorrencia.codigo_acompanhamento_hash and out.codigo_acompanhamento not in ocorrencia.codigo_acompanhamento_hash


async def test_agente_nao_registra_como_canal_publico(registro_policial):
    dto = RegistrarOcorrenciaInput(
        natureza="Furto", descricao="Descrição com mais de vinte caracteres.", localizacao="Centro",
        latitude=-29.78, longitude=-55.79, data_hora_fato=AGORA - timedelta(hours=1), origem=OrigemOcorrencia.PUBLICA,
    )
    with pytest.raises(AcessoNegadoError):
        await registro_policial.executar(AGENTE, dto)


async def test_comunicacao_publica_nao_pode_ser_devolvida(registrar, repositorio):
    out = await registrar.executar(_input())
    ocorrencia = await repositorio.buscar_por_id(out.ocorrencia_id)
    with pytest.raises(TransicaoInvalidaError) as exc:
        ocorrencia.devolver_para_correcao(DELEGADO.id, "Faltam detalhes do fato.", AGORA)
    assert exc.value.chave == "ocorrencia.publica_nao_devolvivel"


async def test_consulta_devolve_apenas_dados_nao_pessoais(registrar, consultar):
    out = await registrar.executar(_input())
    consulta = await consultar.executar(f"  {out.numero_protocolo.lower()} ", out.codigo_acompanhamento.lower())
    assert consulta.numero_protocolo == out.numero_protocolo
    assert consulta.status == "AGUARDANDO_REVISAO" and consulta.natureza == "Furto"
    assert not hasattr(consulta, "desfecho") and not hasattr(consulta, "envolvidos")


@pytest.mark.parametrize("protocolo", ["SGOPI-2026-999999", "", "   "])
async def test_consulta_de_protocolo_inexistente(consultar, protocolo):
    with pytest.raises(EntidadeNaoEncontradaError) as exc:
        await consultar.executar(protocolo, "ABCDEFGHJK")
    assert exc.value.chave == "ocorrencia.protocolo_nao_encontrado"


@pytest.mark.parametrize("codigo", ["", "ERRADO2345", "   "])
async def test_consulta_com_codigo_errado_equivale_a_inexistente(registrar, consultar, codigo):
    out = await registrar.executar(_input())
    with pytest.raises(EntidadeNaoEncontradaError) as exc:
        await consultar.executar(out.numero_protocolo, codigo)
    assert exc.value.chave == "ocorrencia.protocolo_nao_encontrado"


async def test_consulta_nao_alcanca_registro_policial(registro_policial, consultar):
    dto = RegistrarOcorrenciaInput(
        natureza="Furto", descricao="Descrição com mais de vinte caracteres.", localizacao="Centro",
        latitude=-29.78, longitude=-55.79, data_hora_fato=AGORA - timedelta(hours=1),
        envolvidos=(EnvolvidoInputDTO(nome="Vítima", tipo="VITIMA"),),
    )
    out = await registro_policial.executar(AGENTE, dto)
    with pytest.raises(EntidadeNaoEncontradaError):
        await consultar.executar(out.numero_protocolo, "")


async def test_consulta_trata_ocorrencia_excluida_como_inexistente(registrar, consultar, repositorio):
    out = await registrar.executar(_input())
    repositorio._store[out.ocorrencia_id].status = StatusOcorrencia.EXCLUIDA
    with pytest.raises(EntidadeNaoEncontradaError):
        await consultar.executar(out.numero_protocolo, out.codigo_acompanhamento)
