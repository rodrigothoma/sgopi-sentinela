"""
Caso de uso: RegistrarPosicaoViatura (RF16) + detecção de chegada ao local (RF18/RF19).

Chamado tanto pelo adapter HTTP de telemetria quanto pelo simulador — o domínio
não sabe se a posição é real ou simulada (RNF05). Posições não são auditadas
(volume de 1 Hz); a chegada ao local (EM_DESLOCAMENTO → OPERANDO) é, pois muda a
situação da viatura e avisa o Operador que o atendimento começou.

A detecção de chegada é opcional: só acontece quando o caso de uso recebe os
repositórios de ordens e ocorrências (a viatura EM_DESLOCAMENTO chega quando sua
posição fica a até ``raio_chegada_metros`` da ocorrência da ordem ativa).
"""
from __future__ import annotations

from application.ports.inbound.interface_gerir_viaturas import InterfaceRegistrarPosicaoViatura, RegistrarPosicaoInput, ViaturaOutput
from application.ports.outbound.porta_auditoria import PortaAuditoria
from application.ports.outbound.publicador_eventos import PublicadorEventos
from application.ports.outbound.relogio import Relogio
from application.ports.outbound.repositorio_ocorrencia import RepositorioOcorrencia
from application.ports.outbound.repositorio_ordem_despacho import RepositorioOrdemDespacho
from application.ports.outbound.repositorio_viatura import RepositorioViatura
from application.ports.outbound.unidade_de_trabalho import UnidadeDeTrabalho
from application.use_cases.viatura.gerir_viaturas import carregar_viatura, para_output
from domain.auditoria.entity import RegistroAuditoria
from domain.shared.eventos import EventoDominio
from domain.shared.geo import Coordenada
from domain.viatura.entity import SituacaoViatura, Viatura
from domain.viatura.eventos import posicao_atualizada, viatura_chegou_ao_local

RAIO_CHEGADA_PADRAO_METROS = 50.0


class RegistrarPosicaoViatura(InterfaceRegistrarPosicaoViatura):
    def __init__(
        self,
        repositorio: RepositorioViatura,
        uow: UnidadeDeTrabalho,
        relogio: Relogio,
        publicador: PublicadorEventos,
        tolerancia_segundos: int,
        *,
        ordens: RepositorioOrdemDespacho | None = None,
        ocorrencias: RepositorioOcorrencia | None = None,
        auditoria: PortaAuditoria | None = None,
        raio_chegada_metros: float = RAIO_CHEGADA_PADRAO_METROS,
    ) -> None:
        self._repositorio, self._uow, self._relogio, self._publicador, self._tolerancia = repositorio, uow, relogio, publicador, tolerancia_segundos
        self._ordens, self._ocorrencias, self._auditoria = ordens, ocorrencias, auditoria
        self._raio_chegada = raio_chegada_metros

    async def executar(self, input_dto: RegistrarPosicaoInput) -> ViaturaOutput:
        agora = self._relogio.agora()
        coordenada = Coordenada(input_dto.latitude, input_dto.longitude)
        eventos: list[EventoDominio] = []
        async with self._uow:
            viatura = await carregar_viatura(self._repositorio, input_dto.viatura_id)
            viatura.registrar_posicao(coordenada, input_dto.registrada_em, agora, self._tolerancia)
            eventos.append(posicao_atualizada(viatura, agora))
            chegada = await self._detectar_chegada(viatura, agora, input_dto.origem)
            if chegada is not None:
                eventos.append(chegada)
            await self._repositorio.salvar(viatura)
            await self._uow.commit()
        for evento in eventos:
            await self._publicador.publicar(evento)
        return para_output(viatura, agora, self._tolerancia)

    async def _detectar_chegada(self, viatura: Viatura, agora, origem: str | None) -> EventoDominio | None:
        """Viatura EM_DESLOCAMENTO a até ``raio_chegada`` m da ocorrência da ordem ativa → OPERANDO."""
        if viatura.situacao != SituacaoViatura.EM_DESLOCAMENTO or self._ordens is None or self._ocorrencias is None:
            return None
        ordem = await self._ordens.buscar_ativa_por_viatura(viatura.id)
        if ordem is None:
            return None
        ocorrencia = await self._ocorrencias.buscar_por_id(ordem.ocorrencia_id)
        if ocorrencia is None or viatura.ultima_posicao is None:
            return None
        distancia_m = viatura.ultima_posicao.coordenada.distancia_km(ocorrencia.coordenada) * 1000
        if distancia_m > self._raio_chegada:
            return None
        viatura.chegar_ao_local(agora)
        if self._auditoria is not None:
            await self._auditoria.registrar(
                RegistroAuditoria(
                    quem=None, quando=agora, operacao="viatura.chegada_ao_local", entidade="Viatura", entidade_id=str(viatura.id),
                    dados_antes={"situacao": SituacaoViatura.EM_DESLOCAMENTO.value},
                    dados_depois={
                        "situacao": viatura.situacao.value, "ocorrencia_id": str(ocorrencia.id), "numero_ordem": ordem.numero,
                        "distancia_metros": round(distancia_m, 1), "origem": origem,
                    },
                )
            )
        return viatura_chegou_ao_local(
            viatura, agora,
            ocorrencia_id=str(ocorrencia.id), numero_protocolo=ocorrencia.numero_protocolo, numero_ordem=ordem.numero,
            distancia_metros=round(distancia_m, 1),
        )
