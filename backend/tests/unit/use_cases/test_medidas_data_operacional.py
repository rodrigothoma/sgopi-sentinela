"""Regressão: medidas protetivas usam a data do fuso operacional, não a data UTC do instante."""
from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

from application.ports.inbound.interface_gerir_medidas_protetivas import ConcederMedidaInput
from application.use_cases.medida_protetiva.conceder_medida import ConcederMedida
from application.use_cases.medida_protetiva.consultar_medidas import ConsultarMedidas
from domain.ocorrencia.entity import Envolvido, Ocorrencia, TipoEnvolvido
from domain.shared.geo import Coordenada
from tests.fakes.atores import DELEGADO
from tests.fakes.portas_fake import AuditoriaFake, RelogioFake, UnidadeDeTrabalhoFake
from tests.fakes.repositorio_medida_fake import GeradorNumeroMedidaFake, RepositorioMedidaProtetivaFake
from tests.fakes.repositorio_ocorrencia_fake import RepositorioOcorrenciaFake

# 01h30 UTC de 09/11 = 22h30 de 08/11 em America/Sao_Paulo: a data UTC já "virou", a operacional não.
MADRUGADA_UTC = datetime(2026, 11, 9, 1, 30, tzinfo=UTC)
DATA_OPERACIONAL = date(2026, 11, 8)


async def _conceder(prazo_dias: int = 30, data_inicio: date | None = None):
    relogio = RelogioFake(MADRUGADA_UTC)
    repo_oc, repo_medida = RepositorioOcorrenciaFake(), RepositorioMedidaProtetivaFake()
    ocorrencia = Ocorrencia.registrar(
        agente_policial_id=uuid4(),
        natureza="Violência doméstica",
        descricao="Agressão verbal e ameaça no ambiente doméstico.",
        localizacao="Rua General Vitorino, 100",
        coordenada=Coordenada(-29.78, -55.79),
        data_hora_fato=MADRUGADA_UTC - timedelta(hours=2),
        numero_protocolo="SGOPI-2026-000001",
        agora=MADRUGADA_UTC - timedelta(hours=1),
        envolvidos=[Envolvido(nome="Maria", tipo=TipoEnvolvido.VITIMA)],
    )
    await repo_oc.salvar(ocorrencia)
    uc = ConcederMedida(repo_medida, repo_oc, GeradorNumeroMedidaFake(), relogio, UnidadeDeTrabalhoFake(), AuditoriaFake())
    saida = await uc.executar(
        DELEGADO,
        ConcederMedidaInput(
            ocorrencia_id=ocorrencia.id,
            vitima_id=uuid4(),
            agressor_id=uuid4(),
            tipos_restricao=["AFASTAMENTO_DO_LAR"],
            prazo_dias=prazo_dias,
            data_inicio=data_inicio,
        ),
    )
    return saida, repo_medida, relogio


async def test_conceder_sem_data_inicio_usa_data_operacional():
    saida, _, _ = await _conceder()

    assert saida.data_inicio == DATA_OPERACIONAL.isoformat()
    assert saida.dias_restantes == 30


async def test_consulta_calcula_dias_restantes_pela_data_operacional():
    saida, repo_medida, relogio = await _conceder(data_inicio=DATA_OPERACIONAL)

    itens, total = await ConsultarMedidas(repo_medida, relogio).executar(DELEGADO)

    assert total == 1
    assert itens[0].dias_restantes == 30
