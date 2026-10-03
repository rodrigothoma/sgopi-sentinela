"""
Casos de uso para Inteligência Criminal, Manchas Criminais e Alertas de Criticidade (RF05 / UC05 / UC11).
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta
from uuid import UUID

from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_inteligencia_areas_risco import (
    InterfaceCalcularAreasRisco,
    InterfaceConfirmarCienciaAlerta,
    InterfaceEmitirAlertaCriticidade,
)
from application.ports.outbound.porta_auditoria import PortaAuditoria
from application.ports.outbound.publicador_eventos import PublicadorEventos
from application.ports.outbound.relogio import Relogio
from application.ports.outbound.repositorio_notificacao import RepositorioNotificacao
from application.ports.outbound.repositorio_ocorrencia import FiltroOcorrencias, RepositorioOcorrencia
from application.ports.outbound.unidade_de_trabalho import UnidadeDeTrabalho
from domain.auditoria.entity import RegistroAuditoria
from domain.notificacao.entity import Notificacao, PrioridadeNotificacao, TipoNotificacao
from domain.shared.eventos import EventoDominio
from domain.shared.exceptions import EntidadeNaoEncontradaError


def calcular_distancia_metros(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Fórmula de Haversine para distância geodésica em metros."""
    raio_terra = 6371000.0  # metros
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return raio_terra * c


class CalcularAreasRiscoUseCase(InterfaceCalcularAreasRisco):
    def __init__(self, repositorio_ocorrencia: RepositorioOcorrencia, relogio: Relogio) -> None:
        self._repo_ocorrencia = repositorio_ocorrencia
        self._relogio = relogio

    async def executar(self, dias: int = 7) -> list[dict]:
        agora = self._relogio.agora()
        limite_dias = agora - timedelta(days=dias)
        limite_24h = agora - timedelta(hours=24)

        todas = await self._repo_ocorrencia.listar(FiltroOcorrencias(limit=500, mais_recentes_primeiro=True))

        # Filtra ocorrências com coordenadas válidas dentro do período
        validas = [
            o for o in todas
            if o.coordenada is not None
            and o.criada_em >= limite_dias
        ]

        if not validas:
            return []

        # Agrupamento por proximidade (raio de até 1200 metros)
        clusters: list[list] = []
        visitados: set[str] = set()

        for oc in validas:
            oc_id_str = str(oc.id)
            if oc_id_str in visitados:
                continue

            lat1 = oc.coordenada.latitude
            lon1 = oc.coordenada.longitude
            cluster_atual = [oc]
            visitados.add(oc_id_str)

            for vizinha in validas:
                viz_id_str = str(vizinha.id)
                if viz_id_str in visitados:
                    continue
                lat2 = vizinha.coordenada.latitude
                lon2 = vizinha.coordenada.longitude
                dist = calcular_distancia_metros(lat1, lon1, lat2, lon2)
                if dist <= 1200.0:
                    cluster_atual.append(vizinha)
                    visitados.add(viz_id_str)

            clusters.append(cluster_atual)

        # Monta áreas de risco identificadas
        areas_risco = []
        for idx, cluster in enumerate(clusters, start=1):
            total_total = len(cluster)
            ocorrencias_24h = [o for o in cluster if o.criada_em >= limite_24h]
            total_24h = len(ocorrencias_24h)

            # Considera área de risco se houver >= 2 ocorrências em 24h OU >= 3 no período de 7 dias
            if total_24h >= 2 or total_total >= 3:
                lats = [o.coordenada.latitude for o in cluster]
                lons = [o.coordenada.longitude for o in cluster]
                centro_lat = sum(lats) / len(lats)
                centro_lon = sum(lons) / len(lons)

                # Raio dinâmico
                max_dist = max(calcular_distancia_metros(centro_lat, centro_lon, la, lo) for la, lo in zip(lats, lons))
                raio = max(350.0, min(1500.0, max_dist + 150.0))

                # Naturezas predominantes
                naturezas_contagem: dict[str, int] = {}
                for o in cluster:
                    nat = o.natureza or "Diversos"
                    naturezas_contagem[nat] = naturezas_contagem.get(nat, 0) + 1
                principais_naturezas = sorted(naturezas_contagem.keys(), key=lambda k: naturezas_contagem[k], reverse=True)[:3]

                nivel = "CRITICA" if total_24h >= 3 else "ALTA"

                areas_risco.append({
                    "id": f"area-risco-{idx}",
                    "nome": f"Zona Crítica {idx} — {', '.join(principais_naturezas)}",
                    "latitude": round(centro_lat, 6),
                    "longitude": round(centro_lon, 6),
                    "raio_metros": round(raio, 1),
                    "nivel_risco": nivel,
                    "total_ocorrencias": total_total,
                    "total_24h": total_24h,
                    "naturezas_predominantes": principais_naturezas,
                    "protocolos": [o.numero_protocolo for o in cluster],
                })

        return sorted(areas_risco, key=lambda a: (a["total_24h"], a["total_ocorrencias"]), reverse=True)


class EmitirAlertaCriticidadeUseCase(InterfaceEmitirAlertaCriticidade):
    def __init__(
        self,
        repositorio_notificacao: RepositorioNotificacao,
        porta_auditoria: PortaAuditoria,
        publicador_eventos: PublicadorEventos,
        relogio: Relogio,
        uow: UnidadeDeTrabalho | None = None,
    ) -> None:
        self._repo_notif = repositorio_notificacao
        self._porta_auditoria = porta_auditoria
        self._publicador = publicador_eventos
        self._relogio = relogio
        self._uow = uow

    async def executar(self, ator: Ator, dados_alerta: dict) -> dict:
        agora = self._relogio.agora()
        titulo = dados_alerta.get("titulo") or "Alerta de Criticidade em Área de Risco"
        mensagem = dados_alerta.get("mensagem") or "Concentração crítica de ocorrências detectada na mancha criminal."
        papel_destinatario = dados_alerta.get("papel_destinatario") or None
        nivel = dados_alerta.get("nivel_criticidade", "CRITICA")
        prioridade = PrioridadeNotificacao.CRITICA if nivel == "CRITICA" else PrioridadeNotificacao.ALTA

        notif = Notificacao.criar(
            titulo=titulo,
            mensagem=mensagem,
            tipo=TipoNotificacao.ALERTA_CRITICIDADE,
            prioridade=prioridade,
            papel_destinatario=papel_destinatario,
            link="/painel",
            metadados=dados_alerta,
            instante=agora,
        )

        if self._uow:
            async with self._uow:
                salva = await self._repo_notif.salvar(notif)
                await self._porta_auditoria.registrar(
                    RegistroAuditoria(
                        quem=ator.id,
                        quando=agora,
                        operacao="EMISSAO_ALERTA_CRITICIDADE",
                        entidade="inteligencia_criminal",
                        entidade_id=str(salva.id),
                        dados_depois=dados_alerta,
                    )
                )
                await self._uow.commit()
        else:
            salva = await self._repo_notif.salvar(notif)
            await self._porta_auditoria.registrar(
                RegistroAuditoria(
                    quem=ator.id,
                    quando=agora,
                    operacao="EMISSAO_ALERTA_CRITICIDADE",
                    entidade="inteligencia_criminal",
                    entidade_id=str(salva.id),
                    dados_depois=dados_alerta,
                )
            )

        # UC11 / sq11: Disparo de evento via WebSocket
        await self._publicador.publicar(
            EventoDominio(
                tipo="ALERTA_CRITICIDADE",
                ocorrido_em=agora,
                dados={
                    "notificacao_id": str(salva.id),
                    "titulo": salva.titulo,
                    "mensagem": salva.mensagem,
                    "dados": dados_alerta,
                },
            )
        )

        return {
            "alerta_id": str(salva.id),
            "titulo": salva.titulo,
            "status": "EMITIDO",
            "criada_em": salva.criada_em.isoformat(),
        }


class ConfirmarCienciaAlertaUseCase(InterfaceConfirmarCienciaAlerta):
    def __init__(
        self,
        repositorio_notificacao: RepositorioNotificacao,
        porta_auditoria: PortaAuditoria,
        relogio: Relogio,
        uow: UnidadeDeTrabalho | None = None,
    ) -> None:
        self._repo_notif = repositorio_notificacao
        self._porta_auditoria = porta_auditoria
        self._relogio = relogio
        self._uow = uow

    async def executar(self, ator: Ator, alerta_id: str) -> None:
        try:
            uid = UUID(alerta_id)
        except ValueError:
            raise EntidadeNaoEncontradaError(f"ID de alerta inválido: {alerta_id}")

        notif = await self._repo_notif.obter_por_id(uid)
        if notif is None:
            raise EntidadeNaoEncontradaError(f"Alerta {alerta_id} não encontrado.")

        agora = self._relogio.agora()
        notif.marcar_lida(agora)
        papel_str = ator.papel.value if hasattr(ator.papel, "value") else str(ator.papel)

        if self._uow:
            async with self._uow:
                await self._repo_notif.salvar(notif)
                await self._porta_auditoria.registrar(
                    RegistroAuditoria(
                        quem=ator.id,
                        quando=agora,
                        operacao="CIENCIA_ALERTA_CRITICIDADE",
                        entidade="notificacoes",
                        entidade_id=str(uid),
                        dados_depois={"supervisor": ator.login, "papel": papel_str},
                    )
                )
                await self._uow.commit()
        else:
            await self._repo_notif.salvar(notif)
            await self._porta_auditoria.registrar(
                RegistroAuditoria(
                    quem=ator.id,
                    quando=agora,
                    operacao="CIENCIA_ALERTA_CRITICIDADE",
                    entidade="notificacoes",
                    entidade_id=str(uid),
                    dados_depois={"supervisor": ator.login, "papel": papel_str},
                )
            )
