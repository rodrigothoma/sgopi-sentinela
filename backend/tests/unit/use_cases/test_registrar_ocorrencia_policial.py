"""
Testes unitários do caso de uso RegistrarOcorrenciaPolicial.
Usa RepositorioOcorrenciaFake — zero banco, zero servidor.
"""
import pytest
from uuid import uuid4

from application.ports.inbound.interface_registrar_ocorrencia_policial import (
    EnvolvidoInputDTO,
    RegistrarOcorrenciaInput,
    TipificacaoInputDTO,
)
from application.use_cases.ocorrencia.registrar_ocorrencia_policial import RegistrarOcorrenciaPolicial
from tests.fakes.repositorio_ocorrencia_fake import RepositorioOcorrenciaFake


@pytest.fixture
def repositorio():
    return RepositorioOcorrenciaFake()


@pytest.fixture
def use_case(repositorio):
    return RegistrarOcorrenciaPolicial(repositorio)


def _input_valido(**kwargs) -> RegistrarOcorrenciaInput:
    defaults = dict(
        agente_policial_id=uuid4(),
        natureza="Furto",
        descricao="Furto de veículo em via pública",
        localizacao="Av. Brasil, 500",
    )
    defaults.update(kwargs)
    return RegistrarOcorrenciaInput(**defaults)


async def test_registrar_retorna_output_com_protocolo(use_case):
    output = await use_case.executar(_input_valido())
    assert output.numero_protocolo.startswith("SGOPI-")
    assert output.status == "REGISTRADA"


async def test_registrar_persiste_no_repositorio(use_case, repositorio):
    output = await use_case.executar(_input_valido())
    salva = await repositorio.buscar_por_id(output.ocorrencia_id)
    assert salva is not None
    assert salva.numero_protocolo == output.numero_protocolo


async def test_registrar_com_tipificacoes_e_envolvidos(use_case, repositorio):
    inp = _input_valido(
        tipificacoes=(TipificacaoInputDTO(artigo="Art. 155 CP", descricao="Furto simples"),),
        envolvidos=(
            EnvolvidoInputDTO(nome="Maria", tipo="VITIMA"),
            EnvolvidoInputDTO(nome="Carlos", tipo="SUSPEITO", documento="123.456.789-00"),
        ),
    )
    output = await use_case.executar(inp)
    salva = await repositorio.buscar_por_id(output.ocorrencia_id)
    assert len(salva.tipificacoes) == 1
    assert len(salva.envolvidos) == 2


async def test_registrar_descricao_vazia_levanta_valueerror(use_case):
    with pytest.raises(ValueError):
        await use_case.executar(_input_valido(descricao=""))
