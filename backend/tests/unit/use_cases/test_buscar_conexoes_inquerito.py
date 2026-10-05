"""Testes unitários: Motor avançado de busca e sugestão de conexões criminais para inquéritos policiais."""
from datetime import datetime, timedelta, timezone
from uuid import uuid4
import pytest

from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_inteligencia_areas_risco import InterfaceCalcularAreasRisco
from application.ports.outbound.repositorio_ocorrencia import RepositorioOcorrencia
from application.use_cases.inquerito.buscar_conexoes import BuscarConexoesOcorrencia
from domain.ocorrencia.entity import Envolvido, Ocorrencia, TipoEnvolvido, TipificacaoPenal
from domain.ocorrencia.status import StatusOcorrencia
from domain.shared.geo import Coordenada
from domain.usuario.entity import Papel


class FakeRepoOcorrencia(RepositorioOcorrencia):
    def __init__(self, itens: list[Ocorrencia] | None = None) -> None:
        self.itens: list[Ocorrencia] = list(itens or [])

    async def salvar(self, ocorrencia: Ocorrencia) -> None:
        self.itens.append(ocorrencia)

    async def buscar_por_id(self, ocorrencia_id) -> Ocorrencia | None:
        for o in self.itens:
            if o.id == ocorrencia_id:
                return o
        return None

    async def buscar_por_protocolo(self, numero_protocolo) -> Ocorrencia | None:
        for o in self.itens:
            if o.numero_protocolo == numero_protocolo:
                return o
        return None

    async def buscar_por_chave_autenticidade(self, chave) -> Ocorrencia | None:
        return None

    async def buscar_por_hash_narrativa(self, hash_narrativa) -> Ocorrencia | None:
        return None

    async def listar(self, filtro) -> list[Ocorrencia]:
        return [o for o in self.itens if o.status in (filtro.status or (o.status,))]

    async def contar(self, filtro) -> int:
        return len(self.itens)

    async def lacre_em_uso(self, numero_lacre) -> bool:
        return False


class FakeAreasRiscoUC(InterfaceCalcularAreasRisco):
    def __init__(self, areas: list[dict] | None = None) -> None:
        self.areas = areas or []

    async def executar(self, dias: int = 7) -> list[dict]:
        return self.areas


def criar_ocorrencia_validada(
    *,
    protocolo: str,
    natureza: str = "Roubo a Transeunte",
    envolvidos: list[Envolvido] | None = None,
    tipificacoes: list[TipificacaoPenal] | None = None,
    lat: float = -29.7845,
    lon: float = -55.7912,
    horas_atras: int = 2,
) -> Ocorrencia:
    agora = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)
    oc = Ocorrencia.registrar(
        numero_protocolo=protocolo,
        agente_policial_id=uuid4(),
        natureza=natureza,
        descricao="Descrição dos fatos para apuração formal da ocorrência policial.",
        data_hora_fato=agora - timedelta(hours=horas_atras),
        envolvidos=envolvidos or [Envolvido(nome="Vítima Genérica", tipo=TipoEnvolvido.VITIMA)],
        tipificacoes=tipificacoes or [],
        localizacao="Rua dos Andradas, 100, Alegrete",
        coordenada=Coordenada(lat, lon),
        agora=agora - timedelta(hours=horas_atras),
    )
    # Valida a ocorrência para torná-la elegível a inquérito
    oc.validar(delegado_id=uuid4(), em=agora, despacho="Validada formalmente pelo delegado")
    return oc


@pytest.fixture
def ator_delegado() -> Ator:
    return Ator(id=uuid4(), papel=Papel.DELEGADO, login="delegado.teste")


@pytest.mark.asyncio
async def test_conexao_mesmo_suspeito_com_formatacao_diferente_cpf(ator_delegado):
    oc_pivo = criar_ocorrencia_validada(
        protocolo="SGOPI-2026-000001",
        natureza="Roubo a Transeunte",
        envolvidos=[
            Envolvido(nome="Carlos Eduardo", documento="123.456.789-00", tipo=TipoEnvolvido.SUSPEITO),
            Envolvido(nome="Mariana Alves", tipo=TipoEnvolvido.VITIMA),
        ],
    )
    oc_cand = criar_ocorrencia_validada(
        protocolo="SGOPI-2026-000002",
        natureza="Furto Qualificado",
        envolvidos=[
            Envolvido(nome="Carlos Eduardo", documento="12345678900", tipo=TipoEnvolvido.SUSPEITO),
            Envolvido(nome="Outra Vítima", tipo=TipoEnvolvido.VITIMA),
        ],
    )

    repo = FakeRepoOcorrencia([oc_pivo, oc_cand])
    uc = BuscarConexoesOcorrencia(repo)

    conexoes = await uc.executar(ator_delegado, oc_pivo.id)

    assert len(conexoes) == 1
    assert conexoes[0].ocorrencia_id == oc_cand.id
    assert conexoes[0].numero_protocolo == "SGOPI-2026-000002"
    assert conexoes[0].pontuacao_relevancia >= 120
    assert "Mesmo suspeito identificado" in conexoes[0].motivo_conexao


@pytest.mark.asyncio
async def test_conexao_mesma_vitima_reiterada(ator_delegado):
    # Caso de violência doméstica repetida ou perseguição contra a mesma vítima
    oc_pivo = criar_ocorrencia_validada(
        protocolo="SGOPI-2026-000010",
        natureza="Violência Doméstica",
        envolvidos=[
            Envolvido(nome="Maria Aparecida", documento="555.444.333-22", tipo=TipoEnvolvido.VITIMA),
            Envolvido(nome="Agressor A", tipo=TipoEnvolvido.SUSPEITO),
        ],
    )
    oc_cand = criar_ocorrencia_validada(
        protocolo="SGOPI-2026-000011",
        natureza="Ameaça",
        envolvidos=[
            Envolvido(nome="Maria Aparecida", documento="55544433322", tipo=TipoEnvolvido.VITIMA),
            Envolvido(nome="Agressor B", tipo=TipoEnvolvido.SUSPEITO),
        ],
    )

    repo = FakeRepoOcorrencia([oc_pivo, oc_cand])
    uc = BuscarConexoesOcorrencia(repo)

    conexoes = await uc.executar(ator_delegado, oc_pivo.id)

    assert len(conexoes) == 1
    assert conexoes[0].ocorrencia_id == oc_cand.id
    assert conexoes[0].pontuacao_relevancia >= 95
    assert "Mesma vítima identificada" in conexoes[0].motivo_conexao


@pytest.mark.asyncio
async def test_conexao_envolvido_cruzado_suspeito_vitima(ator_delegado):
    # Suspeito em uma ocorrência foi vítima na outra (indício de retaliação / acerto de contas)
    oc_pivo = criar_ocorrencia_validada(
        protocolo="SGOPI-2026-000020",
        natureza="Tentativa de Homicídio",
        envolvidos=[
            Envolvido(nome="João Pedro Lima", documento="777.888.999-00", tipo=TipoEnvolvido.SUSPEITO),
            Envolvido(nome="Vítima X", tipo=TipoEnvolvido.VITIMA),
        ],
    )
    oc_cand = criar_ocorrencia_validada(
        protocolo="SGOPI-2026-000021",
        natureza="Lesão Corporal",
        envolvidos=[
            Envolvido(nome="João Pedro Lima", documento="77788899900", tipo=TipoEnvolvido.VITIMA),
            Envolvido(nome="Outro Infrator", tipo=TipoEnvolvido.SUSPEITO),
        ],
    )

    repo = FakeRepoOcorrencia([oc_pivo, oc_cand])
    uc = BuscarConexoesOcorrencia(repo)

    conexoes = await uc.executar(ator_delegado, oc_pivo.id)

    assert len(conexoes) == 1
    assert conexoes[0].ocorrencia_id == oc_cand.id
    assert conexoes[0].pontuacao_relevancia >= 110
    assert "Envolvido cruzado" in conexoes[0].motivo_conexao
    assert "possível retaliação ou disputa" in conexoes[0].motivo_conexao


@pytest.mark.asyncio
async def test_conexao_mesma_area_de_risco_tatico(ator_delegado):
    oc_pivo = criar_ocorrencia_validada(
        protocolo="SGOPI-2026-000030",
        natureza="Roubo a Transeunte",
        envolvidos=[Envolvido(nome="Vítima Primeira", tipo=TipoEnvolvido.VITIMA)],
        lat=-29.7840,
        lon=-55.7910,
    )
    oc_cand = criar_ocorrencia_validada(
        protocolo="SGOPI-2026-000031",
        natureza="Roubo a Estabelecimento Comercial",
        envolvidos=[Envolvido(nome="Vítima Segunda", tipo=TipoEnvolvido.VITIMA)],
        lat=-29.7842,
        lon=-55.7912,
    )

    areas_fake = FakeAreasRiscoUC([
        {
            "id": "area-1",
            "nome": "Zona Comercial Centro",
            "nivel_risco": "CRITICA",
            "protocolos": ["SGOPI-2026-000030", "SGOPI-2026-000031"],
            "latitude": -29.7841,
            "longitude": -29.7841,
            "raio_metros": 600,
        }
    ])

    repo = FakeRepoOcorrencia([oc_pivo, oc_cand])
    uc = BuscarConexoesOcorrencia(repo, caso_uso_areas_risco=areas_fake)

    conexoes = await uc.executar(ator_delegado, oc_pivo.id)

    assert len(conexoes) == 1
    assert conexoes[0].ocorrencia_id == oc_cand.id
    assert "Ambas ocorreram na mesma Área de Risco: Zona Comercial Centro" in conexoes[0].motivo_conexao
    assert conexoes[0].pontuacao_relevancia >= 50


@pytest.mark.asyncio
async def test_filtro_antiruido_distancia_pura_sem_vinculo_nao_sugere(ator_delegado):
    # Duas ocorrências próximas fisicamente (~1.2km) mas com naturezas e envolvidos completamente desconexos
    oc_pivo = criar_ocorrencia_validada(
        protocolo="SGOPI-2026-000040",
        natureza="Homicídio",
        envolvidos=[
            Envolvido(nome="Pessoa A", documento="111.111.111-11", tipo=TipoEnvolvido.VITIMA),
            Envolvido(nome="Suspeito Desconhecido", tipo=TipoEnvolvido.SUSPEITO),
        ],
        lat=-29.7800,
        lon=-55.7900,
        horas_atras=100,  # Fatos distantes no tempo (> 72h)
    )
    oc_cand = criar_ocorrencia_validada(
        protocolo="SGOPI-2026-000041",
        natureza="Estelionato Eletrônico",
        envolvidos=[
            Envolvido(nome="Pessoa B", documento="222.222.222-22", tipo=TipoEnvolvido.VITIMA),
        ],
        lat=-29.7890,
        lon=-55.7900,
        horas_atras=5,
    )

    repo = FakeRepoOcorrencia([oc_pivo, oc_cand])
    uc = BuscarConexoesOcorrencia(repo)

    conexoes = await uc.executar(ator_delegado, oc_pivo.id)

    # Não deve sugerir falso positivo apenas por estar na mesma cidade/raio
    assert len(conexoes) == 0


@pytest.mark.asyncio
async def test_ordenacao_por_maior_relevancia(ator_delegado):
    oc_pivo = criar_ocorrencia_validada(
        protocolo="SGOPI-2026-000050",
        natureza="Roubo a Transeunte",
        envolvidos=[
            Envolvido(nome="Marcos Silveira", documento="333.444.555-66", tipo=TipoEnvolvido.SUSPEITO),
            Envolvido(nome="Vítima Pivô", tipo=TipoEnvolvido.VITIMA),
        ],
    )
    # Candidata 1: mesmo suspeito (score alto)
    oc_cand_suspeito = criar_ocorrencia_validada(
        protocolo="SGOPI-2026-000051",
        natureza="Roubo a Residência",
        envolvidos=[
            Envolvido(nome="Marcos Silveira", documento="33344455566", tipo=TipoEnvolvido.SUSPEITO),
            Envolvido(nome="Outra Vítima", tipo=TipoEnvolvido.VITIMA),
        ],
    )
    # Candidata 2: mesma natureza apenas (score mais baixo)
    oc_cand_natureza = criar_ocorrencia_validada(
        protocolo="SGOPI-2026-000052",
        natureza="Roubo a Transeunte",
        envolvidos=[
            Envolvido(nome="Outro Infrator", tipo=TipoEnvolvido.SUSPEITO),
            Envolvido(nome="Terceira Vítima", tipo=TipoEnvolvido.VITIMA),
        ],
        lat=-29.7846,
        lon=-55.7913,
        horas_atras=3,
    )

    repo = FakeRepoOcorrencia([oc_pivo, oc_cand_suspeito, oc_cand_natureza])
    uc = BuscarConexoesOcorrencia(repo)

    conexoes = await uc.executar(ator_delegado, oc_pivo.id)

    assert len(conexoes) >= 2
    # A primeira conexão deve ser a do mesmo suspeito (score significativamente mais alto)
    assert conexoes[0].ocorrencia_id == oc_cand_suspeito.id
    assert conexoes[0].pontuacao_relevancia > conexoes[1].pontuacao_relevancia
