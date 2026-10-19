from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from application.ports.inbound.ator import Ator
from application.ports.outbound.porta_auditoria import PortaAuditoria
from application.ports.outbound.publicador_eventos import PublicadorEventos
from application.ports.outbound.relogio import Relogio
from application.ports.outbound.repositorio_notificacao import RepositorioNotificacao
from application.ports.outbound.repositorio_ocorrencia import RepositorioOcorrencia
from application.use_cases.inteligencia.calcular_areas_risco import (
    CalcularAreasRiscoUseCase,
    ConfirmarCienciaAlertaUseCase,
    EmitirAlertaCriticidadeUseCase,
    calcular_distancia_metros,
)
from domain.ocorrencia.entity import Envolvido, Ocorrencia, TipoEnvolvido
from domain.shared.geo import Coordenada
from domain.usuario.entity import Papel


class RelogioFixo(Relogio):
    def agora(self) -> datetime:
        return datetime(2026, 10, 3, 15, 0, 0, tzinfo=timezone.utc)


class RepoOcorrenciaFake(RepositorioOcorrencia):
    def __init__(self) -> None:
        self.itens = []

    async def salvar(self, ocorrencia):
        self.itens.append(ocorrencia)

    async def buscar_por_id(self, ocorrencia_id):
        return None

    async def buscar_por_protocolo(self, numero_protocolo):
        return None

    async def buscar_por_chave_autenticidade(self, chave):
        return None

    async def buscar_por_hash_narrativa(self, hash_narrativa):
        return None

    async def listar(self, filtro):
        return self.itens

    async def contar(self, filtro):
        return len(self.itens)

    async def lacre_em_uso(self, numero_lacre):
        return False


class RepoNotifFake(RepositorioNotificacao):
    def __init__(self) -> None:
        self.itens = {}

    async def registrar_leitura(self, notificacao_id, usuario_id, instante):
        return None

    async def salvar(self, notificacao):
        self.itens[str(notificacao.id)] = notificacao
        return notificacao

    async def obter_por_id(self, notificacao_id):
        return self.itens.get(str(notificacao_id))

    async def listar(self, **kwargs):
        return list(self.itens.values())

    async def contar_nao_lidas(self, **kwargs):
        return len(self.itens)

    async def marcar_todas_lidas(self, usuario_id, papel, instante):
        return len(self.itens)


class AuditoriaFake(PortaAuditoria):
    def __init__(self) -> None:
        self.registros = []

    async def registrar(self, registro) -> None:
        self.registros.append(registro)

    async def listar(self, **kwargs):
        return self.registros


class PublicadorFake(PublicadorEventos):
    def __init__(self) -> None:
        self.eventos = []

    async def publicar(self, evento) -> None:
        self.eventos.append(evento)


def test_calcular_distancia_metros():
    # Coordenadas próximas (~500m) no centro de Porto Alegre / Alegrete
    dist = calcular_distancia_metros(-29.784, -55.791, -29.788, -55.791)
    assert 400 < dist < 500


@pytest.mark.asyncio
async def test_calcular_areas_risco_detecta_cluster_critico():
    rel = RelogioFixo()
    agora = rel.agora()
    repo_oc = RepoOcorrenciaFake()

    # Cria 3 ocorrências concentradas na mesma região nas últimas 24h
    lat_centro, lon_centro = -29.7845, -55.7912
    nomes = ["Maria Silva", "Joana Souza", "Carla Dias"]
    for i in range(3):
        oc = Ocorrencia.registrar(
            numero_protocolo=f"2026-00010{i}",
            agente_policial_id=uuid4(),
            natureza="Roubo a Pedestre",
            descricao="Roubo cometido com grave ameaça em via pública.",
            data_hora_fato=agora - timedelta(hours=2 * i + 1),
            envolvidos=[Envolvido(nome=nomes[i], tipo=TipoEnvolvido.VITIMA)],
            localizacao=f"Rua das Flores, {100 + i}, Centro, Alegrete",
            coordenada=Coordenada(latitude=lat_centro + (i * 0.001), longitude=lon_centro + (i * 0.001)),
            agora=agora - timedelta(hours=i + 1),
        )
        await repo_oc.salvar(oc)

    uc = CalcularAreasRiscoUseCase(repo_oc, rel)
    areas = await uc.executar(dias=7)

    assert len(areas) == 1
    area = areas[0]
    assert area["nivel_risco"] == "CRITICA"
    assert area["total_24h"] == 3
    assert "Roubo a Pedestre" in area["naturezas_predominantes"]


@pytest.mark.asyncio
async def test_emitir_alerta_criticidade_e_confirmar_ciencia():
    rel = RelogioFixo()
    repo_notif = RepoNotifFake()
    porta_audit = AuditoriaFake()
    pub = PublicadorFake()

    ator = Ator(id=uuid4(), papel=Papel.SUPERVISOR, login="supervisor_geral")

    uc_emitir = EmitirAlertaCriticidadeUseCase(repo_notif, porta_audit, pub, rel)
    uc_confirmar = ConfirmarCienciaAlertaUseCase(repo_notif, porta_audit, rel)

    res = await uc_emitir.executar(
        ator=ator,
        dados_alerta={"titulo": "Zona Crítica Centro", "natureza": "Roubo"},
    )
    alerta_id = res["alerta_id"]
    assert res["status"] == "EMITIDO"
    assert len(porta_audit.registros) == 1
    assert porta_audit.registros[0].operacao == "EMISSAO_ALERTA_CRITICIDADE"
    assert len(pub.eventos) == 1

    # Confirma ciência (UC11)
    await uc_confirmar.executar(ator=ator, alerta_id=alerta_id)
    assert len(porta_audit.registros) == 2
    assert porta_audit.registros[1].operacao == "CIENCIA_ALERTA_CRITICIDADE"

    notif = await repo_notif.obter_por_id(alerta_id)
    assert notif.lida is True
