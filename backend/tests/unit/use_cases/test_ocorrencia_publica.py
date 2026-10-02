"""
Testes unitários dos casos de uso do canal público (RF01 — Delegacia Online):
RegistrarOcorrenciaPublica e ConsultarOcorrenciaPublica. Fakes de todas as portas.
"""
from datetime import UTC, datetime, timedelta

import pytest

from application.ports.inbound.interface_registrar_ocorrencia_publica import RegistrarOcorrenciaPublicaInput
from application.use_cases.ocorrencia.consultar_ocorrencia_publica import ConsultarOcorrenciaPublica
from application.use_cases.ocorrencia.registrar_ocorrencia_policial import RegistrarOcorrenciaPolicial
from application.use_cases.ocorrencia.registrar_ocorrencia_publica import RegistrarOcorrenciaPublica
from domain.ocorrencia.entity import TipoEnvolvido
from domain.ocorrencia.status import StatusOcorrencia
from domain.shared.exceptions import EntidadeNaoEncontradaError, ValorInvalidoError
from tests.fakes.atores import AGENTE
from tests.fakes.portas_fake import AuditoriaFake, GeradorProtocoloFake, RelogioFake, UnidadeDeTrabalhoFake
from tests.fakes.repositorio_ocorrencia_fake import RepositorioOcorrenciaFake

AGORA = datetime(2026, 9, 13, 12, 0, tzinfo=UTC)


@pytest.fixture
def repositorio():
    return RepositorioOcorrenciaFake()


@pytest.fixture
def registrar(repositorio):
    registro = RegistrarOcorrenciaPolicial(repositorio, UnidadeDeTrabalhoFake(), RelogioFake(AGORA), GeradorProtocoloFake(), AuditoriaFake())
    return RegistrarOcorrenciaPublica(registro)


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
    out = await registrar.executar(AGENTE, _input())
    ocorrencia = await repositorio.buscar_por_id(out.ocorrencia_id)
    assert out.status == StatusOcorrencia.AGUARDANDO_REVISAO.value
    assert ocorrencia.descricao == "Bicicleta furtada no bicicletário da praça central."
    (comunicante,) = ocorrencia.envolvidos
    assert comunicante.tipo == TipoEnvolvido.COMUNICANTE
    assert (comunicante.nome, comunicante.email) == ("Carlos Alberto", "carlos@exemplo.com")


async def test_recusa_sem_declaracao_de_maioridade(registrar):
    with pytest.raises(ValorInvalidoError) as exc:
        await registrar.executar(AGENTE, _input(declaracao_maioridade=False))
    assert exc.value.chave == "ocorrencia.declaracao_maioridade_ausente"


async def test_recusa_cpf_com_digitos_verificadores_invalidos(registrar):
    with pytest.raises(ValorInvalidoError) as exc:
        await registrar.executar(AGENTE, _input(documento="111.111.111-11"))
    assert exc.value.chave == "envolvido.cpf_comunicante_invalido"


async def test_consulta_devolve_apenas_dados_nao_pessoais(registrar, consultar):
    out = await registrar.executar(AGENTE, _input())
    consulta = await consultar.executar(f"  {out.numero_protocolo.lower()} ")
    assert consulta.numero_protocolo == out.numero_protocolo
    assert consulta.status == "AGUARDANDO_REVISAO" and consulta.natureza == "Furto"
    assert not hasattr(consulta, "desfecho") and not hasattr(consulta, "envolvidos")


@pytest.mark.parametrize("protocolo", ["SGOPI-2026-999999", "", "   "])
async def test_consulta_de_protocolo_inexistente(consultar, protocolo):
    with pytest.raises(EntidadeNaoEncontradaError) as exc:
        await consultar.executar(protocolo)
    assert exc.value.chave == "ocorrencia.protocolo_nao_encontrado"


async def test_consulta_trata_ocorrencia_excluida_como_inexistente(registrar, consultar, repositorio):
    out = await registrar.executar(AGENTE, _input())
    repositorio._store[out.ocorrencia_id].status = StatusOcorrencia.EXCLUIDA
    with pytest.raises(EntidadeNaoEncontradaError):
        await consultar.executar(out.numero_protocolo)
