"""Fixtures compartilhadas dos casos de uso de ocorrência (fakes de todas as portas)."""
from datetime import UTC, datetime, timedelta

import pytest

from application.ports.inbound.interface_registrar_ocorrencia_policial import EnvolvidoInputDTO, RegistrarOcorrenciaInput
from application.use_cases.ocorrencia.registrar_ocorrencia_policial import RegistrarOcorrenciaPolicial
from tests.fakes.atores import AGENTE
from tests.fakes.portas_fake import AuditoriaFake, GeradorProtocoloFake, PublicadorEventosFake, RelogioFake, UnidadeDeTrabalhoFake
from tests.fakes.repositorio_ocorrencia_fake import RepositorioOcorrenciaFake

AGORA = datetime(2026, 9, 13, 12, 0, tzinfo=UTC)


@pytest.fixture
def relogio():
    return RelogioFake(AGORA)


@pytest.fixture
def repositorio():
    return RepositorioOcorrenciaFake()


@pytest.fixture
def uow():
    return UnidadeDeTrabalhoFake()


@pytest.fixture
def auditoria():
    return AuditoriaFake()


@pytest.fixture
def publicador():
    return PublicadorEventosFake()


@pytest.fixture
def deps(repositorio, uow, relogio, auditoria, publicador):
    return (repositorio, uow, relogio, auditoria, publicador)


def input_registro(**kwargs) -> RegistrarOcorrenciaInput:
    defaults = dict(
        natureza="Furto",
        descricao="Furto de veículo em via pública, sem violência.",
        localizacao="Av. Brasil, 500",
        latitude=-29.78,
        longitude=-55.79,
        data_hora_fato=AGORA - timedelta(hours=2),
        envolvidos=(EnvolvidoInputDTO(nome="Maria", tipo="VITIMA", documento="123.456.789-09"),),
    )
    defaults.update(kwargs)
    return RegistrarOcorrenciaInput(**defaults)


@pytest.fixture
async def registrar(repositorio, uow, relogio, auditoria):
    uc = RegistrarOcorrenciaPolicial(repositorio, uow, relogio, GeradorProtocoloFake(), auditoria)

    async def _registrar(ator=AGENTE, **kw):
        return await uc.executar(ator, input_registro(**kw))

    return _registrar
